import wave
import json
from os import path
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer

def vosk_init(mdlfile, framerate):
    model = Model(mdlfile)
    kaldi = KaldiRecognizer(model, framerate)
    return kaldi

def convert_mp3(mp3in, wavout):
    audio = AudioSegment.from_mp3(mp3in)
    audio = audio.set_channels(1)
    audio.export(wavout, format="wav")

def convert_wav(wavin, wavout):
    audio = AudioSegment.from_wav(wavin)
    audio = audio.set_channels(1)
    audio.export(wavout, format="wav")

def Transcriber(mdl, wavin):
    wf = wave.open(wavin, 'rb')
    kaldi = vosk_init(mdl, wf.getframerate())
    kaldi.SetWords(True)

    output = ""

    # recognize audio
    while True:
        clip = wf.readframes(4000)           # read 4000 frames of input
        if(len(clip) == 0): break            # are we done yet?
        if(kaldi.AcceptWaveform(clip)):      # feed frames to recognizer
            output = output + kaldi.Result() # store results

    print(output)