FROM python:3.13-alpine

WORKDIR /app
COPY index.html styles.css app.js ./
COPY backend ./backend
COPY data/seed.json ./data/seed.json
RUN chmod +x /app/backend/entrypoint.sh && \
    addgroup -S airtime && adduser -S airtime -G airtime && \
    mkdir -p /app/data && chown -R airtime:airtime /app

USER airtime

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/health || exit 1

CMD ["/app/backend/entrypoint.sh"]
