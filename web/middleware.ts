import { NextRequest, NextResponse } from "next/server";

const USER = process.env.AUTH_USER ?? "";
const PASS = process.env.AUTH_PASS ?? "";

export function middleware(req: NextRequest) {
  if (!USER || !PASS) return NextResponse.next();

  const header = req.headers.get("authorization") ?? "";
  const [scheme, encoded] = header.split(" ");

  if (scheme === "Basic" && encoded) {
    const [user, pass] = atob(encoded).split(":");
    if (user === USER && pass === PASS) return NextResponse.next();
  }

  return new NextResponse("Unauthorized", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="ProspectMap"' },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
