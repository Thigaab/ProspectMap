"""Audit a website's basic quality from a single HTTP fetch.

Used by the scorer to decide how much "no real web presence" is worth.
A site that's down, HTTP-only, not mobile-friendly, just a Facebook link,
or hosted on a free builder counts as a weak presence — closer to no
website than to a healthy site.
"""
import json
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional
from urllib.parse import urlparse

import requests

import config

FREE_HOSTING_DOMAINS = (
    "wix.com",
    "wixsite.com",
    "weebly.com",
    "e-monsite.com",
    "free.fr",
    "pagesperso-orange.fr",
    "blogspot.com",
    "blogspot.fr",
    "wordpress.com",
    "jimdo.com",
    "jimdofree.com",
    "pagesjaunes.fr",
    "sites.google.com",
    "godaddysites.com",
)

SOCIAL_DOMAINS = (
    "facebook.com",
    "fb.com",
    "fb.me",
    "m.facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "linktr.ee",
)

_VIEWPORT_RE = re.compile(rb"<meta[^>]+name=['\"]?viewport['\"]?", re.IGNORECASE)
_USER_AGENT = (
    "Mozilla/5.0 (compatible; ProspectMap/1.0; +https://github.com/)"
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _domain_matches(host: str, domains: tuple[str, ...]) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


def audit_url(url: str, timeout: float = config.WEB_AUDIT_TIMEOUT) -> dict:
    """Perform a single GET and extract quality signals."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    audit = {
        "url": url,
        "reachable": False,
        "https": parsed.scheme == "https",
        "status_code": None,
        "mobile_viewport": False,
        "social_only": _domain_matches(host, SOCIAL_DOMAINS),
        "free_hosting": _domain_matches(host, FREE_HOSTING_DOMAINS),
        "error": None,
    }

    if not host:
        audit["error"] = "invalid_url"
        return audit

    try:
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )
        audit["status_code"] = resp.status_code
        audit["reachable"] = resp.ok
        final_host = _host(resp.url)
        audit["https"] = urlparse(resp.url).scheme == "https"
        # the *final* host after redirects is what defines social/free-hosting
        if final_host:
            audit["social_only"] = _domain_matches(final_host, SOCIAL_DOMAINS)
            audit["free_hosting"] = _domain_matches(final_host, FREE_HOSTING_DOMAINS)
        if resp.ok:
            sniff = resp.content[:65536]
            audit["mobile_viewport"] = bool(_VIEWPORT_RE.search(sniff))
    except requests.RequestException as e:
        audit["error"] = type(e).__name__

    return audit


def quality_score(audit: Optional[dict]) -> int:
    """Map an audit (or its absence) to a 0–50 web-presence score.

    50 = no website OR effectively no presence (dead site, social-only).
    0  = healthy site: HTTPS, mobile viewport, custom domain.
    """
    max_pts = config.SCORING["no_website_max"]
    if audit is None:
        return max_pts
    if not audit.get("reachable"):
        return max_pts
    if audit.get("social_only"):
        return config.SCORING["weak_web_social_only"]

    score = 0
    if not audit.get("https"):
        score += config.SCORING["weak_web_no_https"]
    if not audit.get("mobile_viewport"):
        score += config.SCORING["weak_web_no_viewport"]
    if audit.get("free_hosting"):
        score += config.SCORING["weak_web_free_hosting"]

    return min(score, max_pts)


def quality_reasons(audit: Optional[dict]) -> list[str]:
    """Human-readable reason codes for the prospect's web-quality bucket."""
    if audit is None:
        return ["no website"]
    if not audit.get("reachable"):
        return ["site unreachable"]
    if audit.get("social_only"):
        return ["social-only"]

    reasons: list[str] = []
    if not audit.get("https"):
        reasons.append("no HTTPS")
    if not audit.get("mobile_viewport"):
        reasons.append("not mobile-friendly")
    if audit.get("free_hosting"):
        reasons.append("free hosting")
    return reasons


def get_cached_audit(
    conn: sqlite3.Connection, url: str, ttl_days: int
) -> Optional[dict]:
    """Return a cached audit if fresh, else None."""
    row = conn.execute(
        "SELECT raw, fetched_at FROM web_audits WHERE url = ?", (url,)
    ).fetchone()
    if not row:
        return None
    fetched_at = datetime.fromisoformat(row["fetched_at"])
    if _utcnow() - fetched_at > timedelta(days=ttl_days):
        return None
    return json.loads(row["raw"])


def save_audit(conn: sqlite3.Connection, audit: dict) -> None:
    conn.execute(
        "INSERT INTO web_audits (url, raw, fetched_at) VALUES (?, ?, ?) "
        "ON CONFLICT(url) DO UPDATE SET "
        "raw = excluded.raw, fetched_at = excluded.fetched_at",
        (audit["url"], json.dumps(audit, ensure_ascii=False), _utcnow().isoformat()),
    )
    conn.commit()


def audit_places(
    conn: sqlite3.Connection,
    places: list[dict],
    ttl_days: int = config.WEB_AUDIT_TTL_DAYS,
    on_progress: Optional[Callable[[str, int, int], None]] = None,
) -> dict[str, Optional[dict]]:
    """Run (cached) audits for every place that has a website.

    Returns {place_id: audit | None}. None means the place has no website
    field at all (caller can interpret it as "no web presence").
    """
    audits: dict[str, Optional[dict]] = {}
    pending: list[tuple[str, str]] = []

    for place in places:
        pid = place.get("place_id")
        if not pid:
            continue
        url = place.get("website")
        if not url:
            audits[pid] = None
            continue
        cached = get_cached_audit(conn, url, ttl_days)
        if cached is not None:
            audits[pid] = cached
        else:
            pending.append((pid, url))

    total = len(pending)
    if total == 0:
        if on_progress:
            on_progress("Web audits (cache hit)", 0, 0)
        return audits

    if on_progress:
        on_progress("Auditing websites", 0, total)

    done = 0
    with ThreadPoolExecutor(max_workers=config.WEB_AUDIT_WORKERS) as pool:
        futures = {pool.submit(audit_url, url): (pid, url) for pid, url in pending}
        for fut in as_completed(futures):
            pid, url = futures[fut]
            try:
                audit = fut.result()
            except Exception as e:  # defensive — should not happen
                audit = {
                    "url": url,
                    "reachable": False,
                    "https": False,
                    "status_code": None,
                    "mobile_viewport": False,
                    "social_only": False,
                    "free_hosting": False,
                    "error": type(e).__name__,
                }
            audits[pid] = audit
            save_audit(conn, audit)
            done += 1
            if on_progress:
                on_progress("Auditing websites", done, total)

    return audits
