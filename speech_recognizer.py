#!/usr/bin/env python3
import wave
import json
import rpyc
import time
from os import path
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer

# initialize Vosk model and Kaldi recognizer
def vosk_init(mdlfile, framerate):
    model = Model(mdlfile)
    kaldi = KaldiRecognizer(model, framerate)
    return kaldi

# convert mp3 to mono wav
def convert_mp3(mp3in, wavout):
    audio = AudioSegment.from_mp3(mp3in)
    audio = audio.set_channels(1)
    audio.export(wavout, format="wav")

# convert stereo wav to mono wav
def convert_wav(wavin, wavout):
    audio = AudioSegment.from_wav(wavin)
    audio = audio.set_channels(1)
    audio.export(wavout, format="wav")

# transcribe audio, given model filename and wav filename
def transcriber(model_file, wav_filename):
    wf = wave.open(wav_filename, 'rb')
    kaldi = vosk_init(model_file, wf.getframerate())
    kaldi.SetWords(True)
    output = ""
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

class TranscriberSvc(rpyc.Service):
    def on_connect(self, conn):
        self.conn = conn
        pass

    def on_disconnect(self, conn):
        pass

    def exposed_do_transcribe(self, tid, ext):
        with open("test.txt", "a") as file:
            time.sleep(10)
            file.write(tid)
        
        return "worked"

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(TranscriberSvc, port=18861)
    t.start()