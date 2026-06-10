# Rumah123 listing-extractor API (FastAPI).
#
# The API imports the `scraper` package, so build from the REPO ROOT (not api/):
#   docker build -f api/Dockerfile -t collateral_scrapping .
#   docker run -p 9000:9000 -e GOOGLE_MAPS_API_KEY=AIza... collateral_scrapping
#
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=9000

WORKDIR /app

# Install dependencies first so this layer caches unless pyproject/scraper change.
# (Building the project needs pyproject.toml + the scraper package.)
COPY pyproject.toml ./
COPY scraper/ ./scraper/
RUN pip install ".[api]"

# App code last — it changes most often.
COPY api/ ./api/

# Run as a non-root user.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://127.0.0.1:9000/health',timeout=4).status_code==200 else 1)"

# exec via sh so ${PORT} expands AND signals (SIGTERM) reach uvicorn for clean shutdown.
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
