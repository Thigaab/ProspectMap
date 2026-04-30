FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY cli/ ./cli/
COPY api/ ./api/
ENV PROSPECTMAP_DB=/data/prospects.db
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
