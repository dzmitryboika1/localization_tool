import os
from glob import glob
from io import BytesIO
from zipfile import ZipFile

from dotenv import load_dotenv
from flask import Flask, send_from_directory, render_template, request, redirect, url_for, flash, session, send_file
from flask_bootstrap import Bootstrap
from flask_dropzone import Dropzone
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.utils import secure_filename

from localization_tool.translator import localize_arb_file

load_dotenv()

app = Flask(__name__)
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
    DROPZONE_DEFAULT_MESSAGE='Drop your .arb files here to upload (max size up to 1 MB)',
    DROPZONE_INVALID_FILE_TYPE="Can't upload files of this type. Only .arb files are allowed",
    DROPZONE_UPLOAD_MULTIPLE=False,
    DROPZONE_ENABLE_CSRF=True,
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['DROPZONE_ALLOWED_FILE_TYPE']


@app.route('/')
def home():
    return render_template("index.html", arb_translated=request.args.get('arb_translated'))


@app.route('/upload-arb', methods=["POST", "GET"])
def upload_arb():
    if request.method == 'POST':
        # check if the post request has the files
        if "file" not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        source_arb_files = request.files.getlist("file")
        session['source_arb_file_names'] = []
        for file in source_arb_files:
            # if the user does not drop a file, the browser submits an empty file without a filename.
            if file.filename == '':
                flash('No selected files', 'error')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                # safely extract the original filename
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                session['source_arb_file_names'].append(filename)
                return redirect(url_for('translate'))

        return redirect(url_for('home'))


@app.route('/translate')
def translate():
    source_arb_file_names = session.get('source_arb_file_names', None)
    if source_arb_file_names:
        for file in source_arb_file_names:
            path_to_source_arb = f"{app.config['UPLOAD_FOLDER']}/{file}"
            output_arb_file_path = localize_arb_file(path_to_source_arb, app.config['DOWNLOAD_FOLDER'])
            if output_arb_file_path:
                session['output_arb_file_path'] = output_arb_file_path
                return redirect(url_for('home', arb_translated=True))

            flash('Oops, something went wrong. Please, try again!', 'error')
            return redirect(url_for('home'))

    flash('Please, upload files!', 'error')
    return redirect(url_for('home'))


@app.route('/download')
def download():
    target = app.config['DOWNLOAD_FOLDER']
    if len(glob(f"{target}/*.arb")) > 1:
        print('hi')
        stream = BytesIO()
        with ZipFile(stream, 'w') as zip_file:
            for file in glob(os.path.join(target, '*.arb')):
                zip_file.write(file, os.path.basename(file))
        stream.seek(0)
        return send_file(stream, as_attachment=True, download_name='archive.zip')

    return send_from_directory(
        directory=app.config['DOWNLOAD_FOLDER'],
        path=os.path.basename(glob(os.path.join(target, '*.arb'))[0]),
        as_attachment=True
    )


# handle CSRF error
@app.errorhandler(CSRFError)
def csrf_error(error):
    return error.description, 400


if __name__ == '__main__':
    app.run()
