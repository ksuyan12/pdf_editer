import os
import shutil
import tempfile
import zipfile

from flask import Flask, render_template, request, send_file, abort

import main as pdf

app = Flask(__name__)


def save_upload(file_storage):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    file_storage.save(tmp.name)
    return tmp


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/merge', methods=['POST'])
def merge():
    files = request.files.getlist('files')
    if not files:
        abort(400, 'No files provided')
    uploads = [save_upload(f) for f in files]
    output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.merge_pdfs(output.name, [u.name for u in uploads])
    for u in uploads:
        os.unlink(u.name)
    return send_file(output.name, as_attachment=True, download_name='merged.pdf')


@app.route('/split', methods=['POST'])
def split():
    file = request.files.get('file')
    if not file:
        abort(400, 'No file provided')
    start = request.form.get('start')
    end = request.form.get('end')
    start = int(start) if start else None
    end = int(end) if end else None

    upload = save_upload(file)
    out_dir = tempfile.mkdtemp()
    prefix = os.path.join(out_dir, 'split')
    pdf.split_pdf(upload.name, prefix, start, end)

    zip_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    with zipfile.ZipFile(zip_tmp.name, 'w') as zf:
        for fname in sorted(os.listdir(out_dir)):
            zf.write(os.path.join(out_dir, fname), fname)
    shutil.rmtree(out_dir)
    os.unlink(upload.name)
    return send_file(zip_tmp.name, as_attachment=True, download_name='split.zip')


@app.route('/rotate', methods=['POST'])
def rotate():
    file = request.files.get('file')
    if not file:
        abort(400, 'No file provided')
    angle = int(request.form.get('angle', 90))
    upload = save_upload(file)
    output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.rotate_pages(upload.name, output.name, angle)
    os.unlink(upload.name)
    return send_file(output.name, as_attachment=True, download_name='rotated.pdf')


@app.route('/remove', methods=['POST'])
def remove():
    file = request.files.get('file')
    if not file:
        abort(400, 'No file provided')
    pages = request.form.get('pages', '')
    pages = [int(p.strip()) for p in pages.split(',') if p.strip().isdigit()]
    upload = save_upload(file)
    output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.remove_pages(upload.name, output.name, pages)
    os.unlink(upload.name)
    return send_file(output.name, as_attachment=True, download_name='removed.pdf')


@app.route('/add_text', methods=['POST'])
def add_text():
    file = request.files.get('file')
    if not file:
        abort(400, 'No file provided')
    text = request.form.get('text', '')
    x = float(request.form.get('x', 100))
    y = float(request.form.get('y', 750))
    page_num = int(request.form.get('page', 0))
    upload = save_upload(file)
    output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.add_text(upload.name, output.name, text, x, y, page_num)
    os.unlink(upload.name)
    return send_file(output.name, as_attachment=True, download_name='text.pdf')


@app.route('/watermark', methods=['POST'])
def watermark():
    file = request.files.get('file')
    watermark_file = request.files.get('watermark')
    if not file or not watermark_file:
        abort(400, 'File or watermark missing')
    pdf_file = save_upload(file)
    wm_file = save_upload(watermark_file)
    output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.apply_watermark(pdf_file.name, wm_file.name, output.name)
    os.unlink(pdf_file.name)
    os.unlink(wm_file.name)
    return send_file(output.name, as_attachment=True, download_name='watermarked.pdf')


if __name__ == '__main__':
    app.run(debug=True)
