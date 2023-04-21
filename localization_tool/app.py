import os
import time

from dotenv import load_dotenv
from flask import Flask, send_from_directory, render_template, request, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from flask_dropzone import Dropzone
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.utils import secure_filename
# from celery_utils import get_celery_app_instance

from localization_tool.translator import localize_arb_file

load_dotenv()

app = Flask(__name__)
# celery = get_celery_app_instance(app)
csrf = CSRFProtect(app)
bootstrap = Bootstrap(app)
dropzone = Dropzone(app)

app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    UPLOAD_FOLDER='to_upload', DOWNLOAD_FOLDER='to_download',
    DROPZONE_MAX_FILE_SIZE=1,  # Mb
    DROPZONE_MAX_FILES=5,
    DROPZONE_ALLOWED_FILE_CUSTOM=True,
    DROPZONE_ALLOWED_FILE_TYPE='.arb',
    DROPZONE_DEFAULT_MESSAGE='Drop your .arb file here to to_upload (max size up to 1 MB)',
    DROPZONE_INVALID_FILE_TYPE="Can't upload files of this type.",
    DROPZONE_UPLOAD_MULTIPLE=False, DROPZONE_ENABLE_CSRF=True,
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['DROPZONE_ALLOWED_FILE_TYPE']


@app.route('/')
def home():
    return render_template("index.html", arb_translated=request.args.get('arb_translated'))


@app.route('/upload-arb', methods=["POST", "GET"])
def upload_arb():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        source_arb_file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if source_arb_file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if source_arb_file and allowed_file(source_arb_file.filename):
            filename = secure_filename(source_arb_file.filename)
            source_arb_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            session['source_arb_file_name'] = filename
            return redirect(url_for('translate'))

        return redirect(url_for('home'))


@app.route('/translate')
def translate():
    source_arb_file_name = session.get('source_arb_file_name', None)
    if source_arb_file_name:
        path_to_source_arb = f"{app.config['UPLOAD_FOLDER']}/{source_arb_file_name}"
        output_arb_file_path = localize_arb_file(path_to_source_arb, app.config['DOWNLOAD_FOLDER'])
        if output_arb_file_path:
            session['output_arb_file_path'] = output_arb_file_path
            return redirect(url_for('home', arb_translated=True))
        flash('Oops, something went wrong. Please, try again!', 'error')
        return redirect(url_for('home'))

    flash('Please, upload file!', 'error')
    return redirect(url_for('home'))


@app.route('/download')
def download():
    # function.delay() is used to trigger function as celery task
    # clear_uploads_downloads_dirs.delay()
    return send_from_directory(
        directory=app.config['DOWNLOAD_FOLDER'],
        path=os.path.basename(session['output_arb_file_path']),
        as_attachment=True
    )


# handle CSRF error
@app.errorhandler(CSRFError)
def csrf_error(e):
    return e.description, 400


# celery tasks
# @celery.task
# def clear_uploads_downloads_dirs():
#     time.sleep(60)
#     os.remove(f"{app.config['UPLOAD_FOLDER']}/{session['pdf_file_name']}")
#     os.remove(f"{app.config['DOWNLOAD_FOLDER']}/{session['mp3_file_name']}")
#     return "Task completed!"


if __name__ == '__main__':
    app.run()
