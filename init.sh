#!/bin/sh
# https://github.com/coqui-ai/TTS --> Text to Speech
# https://github.com/alphacep/vosk-api --> Speech to Text

# start backend (transcriber)
python3 speech_recognizer.py &

# start frontend (flask)
gunicorn --bind ${HOST}:${PORT} wsgi:app