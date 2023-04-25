#!/bin/sh
# https://github.com/coqui-ai/TTS --> Text to Speech
# https://github.com/alphacep/vosk-api --> Speech to Text

# save firebase cred
mkdir -p private
echo "$FIREBASE_CRED" | base64 -d > private/firebase_cred.json

mkdir -p upload/audio results static

# start message queue (redis)
service redis-server start

# start backend (celery) in background
celery -A app.celery worker --loglevel=info --pidfile=/tmp/celery-worker.pid -f /tmp/celery-worker.log -D

# start frontend (flask)
gunicorn -p /tmp/gunicorn.pid --bind ${HOST}:${PORT} wsgi:app