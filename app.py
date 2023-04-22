from flask import Flask, render_template, request, url_for, flash, redirect, session
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import os
import uuid

DEBUG = True
UPLOAD_FOLDER = 'upload'
ALLOWED_EXTENSIONS_AUDIO = {'mp3', 'wav', 'ogg', 'm4a'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1000 * 1000
app.config['SECRET_KEY'] = str(uuid.uuid1())

def get_suffix(fn):
    x = fn.split('.')
    return x[len(x)-1]

def file_allowed(fn, allowed):
    if get_suffix(fn) in allowed:
        return True
    return False

def debug_print(msg):
    if(DEBUG == True):
        print("DEBUG: " + msg)
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/result')
def transcribe_results():
    tid = request.args['tid']
    tid = session['tid']
    return render_template("transcribe_results.html", tid=tid)

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
            rand_str = str(uuid.uuid1())
            debug_print("uploaded file: " + rand_str)
            filename = rand_str + '.' + get_suffix(secure_filename(file.filename))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            session['tid'] = filename
            return redirect(url_for('.transcribe_results', tid=filename))
        else:
            debug_print("Invalid file extension")
            flash("Invalid File Extension")
            return redirect(request.url)
    debug_print("Upload page: " + request.method)
    return render_template("transcribe_upload.html")


if __name__ == "__main__":
    app.run()