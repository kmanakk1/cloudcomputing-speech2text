#!/usr/bin/env python3
import wave
import json
import time
from os import path, getenv
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer

# Helper functions
def get_env(key, default):
    res = getenv(key)
    if res == None: return default
    return res

def get_suffix(fn):
    x = fn.split('.')
    return x[len(x)-1]

# confirm suffix
def file_allowed(fn, allowed):
    if get_suffix(fn) in allowed:
        return True
    return False

# convert mp3 to mono wav
def convert_mp3(mp3in, wavout):
    audio = AudioSegment.from_mp3(mp3in)
    audio = audio.set_channels(1)
    audio.export(wavout, format="wav")
