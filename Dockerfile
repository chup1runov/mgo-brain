FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MGO_BRAIN_HOST=0.0.0.0 \
    MGO_BRAIN_DATA_DIR=/var/lib/mgo-brain

WORKDIR /build
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY mgo_brain ./mgo_brain

RUN pip install --no-cache-dir '.[analytics]' \
    && groupadd --gid 10001 mgo \
    && useradd --uid 10001 --gid mgo --no-create-home mgo \
    && mkdir -p /var/lib/mgo-brain \
    && chown mgo:mgo /var/lib/mgo-brain \
    && rm -rf /build/*

WORKDIR /var/lib/mgo-brain
USER 10001:10001
EXPOSE 8080
CMD ["mgo-brain"]
