# syntax=docker/dockerfile:1

# ---------- build stage: install dependencies into a virtualenv ----------
FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- runtime stage: only the venv and the app, running as non-root ----------
FROM python:3.12-slim AS runtime

# Build metadata, injected by CI so every image can be traced back to a commit.
ARG APP_VERSION=dev
ARG GIT_SHA=unknown
ARG BUILD_TIME=unknown
LABEL org.opencontainers.image.title="taskflow" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      org.opencontainers.image.created="${BUILD_TIME}"

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION} \
    GIT_SHA=${GIT_SHA} \
    BUILD_TIME=${BUILD_TIME}

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /srv
COPY --from=build /opt/venv /opt/venv
COPY --chown=root:root app ./app

# Numeric UID so Kubernetes can verify runAsNonRoot.
USER 10001
EXPOSE 8000

# One uvicorn worker per container: Kubernetes scales by adding pods (replicas),
# which keeps metrics per-process simple and lets the HPA do the scaling.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--timeout-graceful-shutdown", "20"]
