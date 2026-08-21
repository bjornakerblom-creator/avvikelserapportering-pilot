# Container image for running Avvikelserapportering on a Linux host (e.g. Render.com)
# for pilot/testing purposes. The everyday Windows workflow (setup.bat / run_app.bat)
# is unaffected by this file.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

# Data (SQLite db + uploaded attachments) lives here inside the container.
# On Render's free tier this has NO persistent disk attached, so it is wiped
# whenever the service restarts/redeploys/wakes from sleep - fine for a short
# pilot test with dummy data, not for anything that must be kept.
ENV AVVIKELSER_DATA_DIR=/data
RUN mkdir -p /data

# Render injects $PORT at runtime; default to 8600 for local `docker run`.
ENV PORT=8600
EXPOSE 8600

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
