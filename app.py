from flask import Flask, render_template, request, url_for, flash, redirect, session, jsonify, make_response
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from celery import Celery
from helper import convert_mp3, file_allowed, get_suffix, get_env
from firebase_admin import db, credentials
import firebase_admin, os, uuid
import wave, json
from os import path
from vosk import Model, KaldiRecognizer

DEBUG = True
UPLOAD_FOLDER = 'upload/audio'
ALLOWED_EXTENSIONS_AUDIO = {'mp3', 'wav'}

# flask config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 128 * 1000 * 1000
app.config['SECRET_KEY'] = str(uuid.uuid1())

# celery config
REDIS_URL = get_env('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_BROKER_URL'] = REDIS_URL
app.config['CELERY_result_backend'] = REDIS_URL

# firebase config
firebase_cred = credentials.Certificate("private/firebase_cred.json")
firebase_admin.initialize_app(firebase_cred, {
    'databaseURL': get_env('FIREBASE_URL', 'https://speechbackend-74730-default-rtdb.firebaseio.com/')
})

# vosk config
VOSK_MODEL = 'models/vosk-model-small-en-us-0.15'    # path to vosk

# create celery object
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

def debug_print(msg):
    if(DEBUG == True):
        print("DEBUG: " + msg)

# Celery Tasks
# do transcriptions in the background
@celery.task
def async_transcriber(task_id, task_ext, name):
    # DEBUG
    print("DEBUG: got task: " + task_id)

    # reference firebase
    ref = db.reference("/Tasks")

    # initialize firebase reference
    ref.update({
        task_id: {
            "text": "",
            "name": name,
            "finished": False,
            "progress": 0,
        }
    })

    # get filename from task_id
    filename_base = UPLOAD_FOLDER + '/' + task_id
    filename = filename_base + '.' + task_ext

    # if needed, convert input audio to wav format
    if task_ext == 'mp3':
        convert_mp3(filename, filename_base + '.wav')       # convert mp3 to wav
        os.remove(filename)                                 # remove old mp3
        filename = filename_base + '.wav'
        
    # do transcription
    wf = wave.open(filename, 'rb')                      # open wav file
    model = Model(VOSK_MODEL)                           # load Vosk model
    kaldi = KaldiRecognizer(model, wf.getframerate())   # initialize Kaldi recognizer with the same framerate as model
    kaldi.SetWords(True)
    result_text = ""                                    # save output from recognizer
    total_frames = wf.getnframes()                      # get total frames
    current_frame = 0                                   # keep track of current frame
    progress = 0                                        # track progress
    hundredth = total_frames/100

    # recognize audio
    while True:
        current_frame += 4000
        clip = wf.readframes(4000)           # read 4000 frames of input
        if(len(clip) == 0): break            # are we done yet?
        if(kaldi.AcceptWaveform(clip)):      # feed frames to recognizer
            kaldi_res = kaldi.Result()
            new_text = json.loads(kaldi_res).get("text", "")
            if not new_text == "":
                result_text = result_text + " " + new_text
            if(current_frame >= progress*hundredth):
                # we upload snippets while transcribing, for a fancier web view
                ref.child(task_id).update({"text": result_text, "progress": (current_frame/total_frames)*100, "finished": False})
                progress += 1

    # add final result to output
    result_text = result_text + json.loads(kaldi.FinalResult()).get("text", "")
    kaldi = None

    # clean up residual wav file
    os.remove(filename)

    # update firebase
    ref.child(task_id).update({"text": result_text, "finished": True, "progress": 100})

    # debug: write output to file
    try:
        out = open('results/' + task_id, "w")
        out.write(result_text)
        out.close()
    except:
        print("could not open file")
    return

# Routes
@app.route('/')
def index():
    return redirect(url_for('.upload'))

@app.route('/json')
def transcribe_json():
    task_id = request.args['task_id']
    ref = db.reference("/Tasks")
    task = ref.child(task_id).get()
    return jsonify(task)

@app.route('/text/<var>')
def get_text(var):
    task_id = var.split('.')[0]
    ref = db.reference("/Tasks")
    task = ref.child(task_id).get()
    text = "Invalid task id"
    if task: text = task['text']

    response = make_response(text, 200)
    response.mimetype = "text/plain"
    return response

@app.route('/results')
def results():
    # query firebase
    task_id = request.args['task_id']
    ref = db.reference("/Tasks")
    task = ref.child(task_id).get()

    progress = 0
    name = "Waiting..."
    # check results
    if task:
        progress = task['progress']
        name = task['name']
        # if task is done, show results
        if task['finished']:
            return render_template("results.html", task_name=name, results=task['text'], waitprogress=100, task_id=task_id)

    # task not in db, or not done yet, wait.
    return render_template("results.html", task_name=name, task_id=task_id, waitprogress=progress)

@app.route('/upload', methods=["POST", "GET"])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            debug_print("No file part")
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            debug_print("No file selected")
            flash("No file selected")
            return redirect(request.url)
        
        # if file is allowed, start transcription task and send user to waiting page
        if file and file_allowed(file.filename, ALLOWED_EXTENSIONS_AUDIO):
            # assign the task a random uuid
            task_id = str(uuid.uuid1())
            task_ext = get_suffix(secure_filename(file.filename))
            task_name = secure_filename(file.filename)
            debug_print("uploaded file: " + task_id)

            # accept uploaded file
            filename = task_id + '.' + task_ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Asynchronously do transcription
            async_transcriber.delay(task_id, task_ext, task_name)

            # redirect to results page
            return redirect(url_for('.results', task_id=task_id))
        else:
            # else, file was not allowed: inform user of their error
            flash("Invalid File Extension")
            return redirect(request.url)
    return render_template("upload.html")


if __name__ == "__main__":
    app.run()