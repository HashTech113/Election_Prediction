# Kerala Election 2026 backend — minimal runtime image.
#
# main.py + services.py + schemas.py + routers/ only need fastapi / uvicorn /
# pydantic + stdlib. Heavier deps (torch, transformers, sklearn, pandas,
# numpy, tqdm) in requirements.txt are only used by training / preprocessing
# scripts that never run on Railway, so they are intentionally not installed
# here.
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install \
    "fastapi>=0.110.0,<0.120.0" \
    "uvicorn[standard]>=0.29.0,<0.40.0" \
    "pydantic>=2.6.0,<3.0.0"

# Build context = backend/kerala/ (Railway "Root Directory" setting).
# Copy everything; .dockerignore strips out caches and large model artefacts.
COPY . /app/

# Railway injects $PORT at runtime. Default to 8000 for `docker run`.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
