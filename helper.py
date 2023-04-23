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

# convert stereo wav to mono wav
#def convert_wav(wavin, wavout):
#    audio = AudioSegment.from_wav(wavin)
#    audio = audio.set_channels(1)
#    audio.export(wavout, format="wav")

# transcribe audio, given model filename and wav filename
def vosk_transcribe(model_file, wav_filename):
    wf = wave.open(wav_filename, 'rb')                  # open wav file
    model = Model(model_file)                           # load Vosk model
    kaldi = KaldiRecognizer(model, wf.getframerate())   # initialize Kaldi recognizer with the same framerate as model
    kaldi.SetWords(True)
    output = ""                                         # save output from recognizer
    # recognize audio
    while True:
        clip = wf.readframes(4000)           # read 4000 frames of input
        if(len(clip) == 0): break            # are we done yet?
        if(kaldi.AcceptWaveform(clip)):      # feed frames to recognizer
            output = output + kaldi.Result() # store results
    output = output + kaldi.FinalResult()    # add final result to output
    outputDict = json.loads(output)          # load output as json
    outputText = outputDict.get("text", "")  # get text from audio as full string
    kaldi = None
    return outputText