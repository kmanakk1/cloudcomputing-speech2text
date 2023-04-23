from flask import Flask, render_template, request, url_for, flash, redirect, session
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from celery import Celery
from helper import vosk_transcribe, convert_mp3, file_allowed, get_suffix
import os
import uuid

DEBUG = True
UPLOAD_FOLDER = 'upload/audio'
ALLOWED_EXTENSIONS_AUDIO = {'mp3', 'wav'}

# flask config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1000 * 1000
app.config['SECRET_KEY'] = str(uuid.uuid1())

# celery config
REDIS_URL = 'redis://localhost:6379/0'
app.config['CELERY_BROKER_URL'] = REDIS_URL
app.config['CELERY_RESULT_BACKEND'] = REDIS_URL

# create celery object
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

def debug_print(msg):
    if(DEBUG == True):
        print("DEBUG: " + msg)

# Celery Tasks
# do transcriptions in the background
@celery.task
def async_transcriber(task_id, task_ext):
    # DEBUG
    print("DEBUG: got task: " + task_id)

    # get filename from task_id
    filename_base = UPLOAD_FOLDER + '/' + task_id
    filename = filename_base + '.' + task_ext

    # if needed, convert input audio to wav format
    if task_ext == 'mp3':
        convert_mp3(filename, filename_base + '.wav')       # convert mp3 to wav
        os.remove(filename)                                 # remove old mp3
        filename = filename_base + '.wav'
        
    # do transcription
    results = vosk_transcribe(MODEL, filename)              # do transcription (with Vosk)
    os.remove(filename)                                     # clean up residual wav file

    # debug: write output to file
    out = open('results/' + task_id, "w")
    out.write(results)
    out.close()
    return

# Routes
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/result')
def transcribe_results():
    task_id = request.args['task_id']
    #task_id = session['task_id']
    #task_ext = session['task_ext']
    return render_template("transcribe_results.html", task_id=task_id)

@app.route('/transcribe', methods=["POST", "GET"])
def transcribe_upload():
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
        
        debug_print(file.filename)
        if file and file_allowed(file.filename, ALLOWED_EXTENSIONS_AUDIO):
            # assign the task a random uuid
            task_id = str(uuid.uuid1())
            task_ext = get_suffix(secure_filename(file.filename))

            debug_print("uploaded file: " + task_id)

            # accept uploaded file
            filename = task_id + '.' + task_ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # connect to backend if needed
            backend = rpyc.connect(BACKEND_HOST, BACKEND_PORT)

            # do transcription on backend
            doTranscribe = rpyc.async_(backend.root.do_transcribe)
            doTranscribe(task_id, task_ext)

            # keep track of task identifier
            #session['task_id'] = task_id
            #session['task_ext'] = task_ext

            # redirect to results page
            return redirect(url_for('.transcribe_results', task_id=task_id, task_ext=task_ext))

        else:
            debug_print("Invalid file extension")
            flash("Invalid File Extension")
            return redirect(request.url)
    debug_print("Upload page: " + request.method)
    return render_template("transcribe_upload.html")


if __name__ == "__main__":
    app.run()


    # use celery to run transcription in bg
    # https://docs.celeryq.dev/en/stable/