FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy only pyproject.toml first to cache dependency layer
COPY pyproject.toml .
# Install all runtime + dev deps without the package itself
RUN pip install --no-cache-dir \
    fastapi>=0.111.0 \
    "uvicorn[standard]>=0.30.0" \
    gunicorn>=22.0.0 \
    pydantic-settings>=2.3.0 \
    sqlalchemy>=2.0.30 \
    psycopg2-binary>=2.9.9 \
    alembic>=1.13.0 \
    "celery[redis]>=5.4.0" \
    boto3>=1.34.0 \
    "python-jose[cryptography]>=3.3.0" \
    httpx>=0.27.0 \
    python-multipart>=0.0.9 \
    pytest>=8.2.0 \
    pytest-postgresql>=6.0.0 \
    pytest-mock>=3.14.0 \
    freezegun>=1.5.0 \
    ruff>=0.5.0 \
    mypy>=1.10.0 \
    types-python-jose

# Copy source code
COPY . .

# Install the package in editable mode (now source is present)
RUN pip install --no-cache-dir -e . --no-deps

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
