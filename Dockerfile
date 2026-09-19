FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MGO_BRAIN_HOST=0.0.0.0 \
    MGO_BRAIN_DATA_DIR=/var/lib/mgo-brain

WORKDIR /app
COPY pyproject.toml README.md ./
COPY mgo_brain ./mgo_brain
COPY config ./config
COPY static ./static

# Runtime files and secrets are never copied from the build context.
RUN pip install --no-cache-dir -e '.[analytics]' \
    && groupadd --gid 10001 mgo \
    && useradd --uid 10001 --gid mgo --no-create-home mgo \
    && mkdir -p /var/lib/mgo-brain \
    && chown mgo:mgo /var/lib/mgo-brain

USER 10001:10001
EXPOSE 8080
CMD ["mgo-brain"]
