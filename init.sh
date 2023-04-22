#!/bin/sh
# https://github.com/coqui-ai/TTS --> Text to Speech
# https://github.com/alphacep/vosk-api --> Speech to Text
gunicorn --bind ${HOST}:${PORT} wsgi:app