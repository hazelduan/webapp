
from flask import render_template, url_for, request
from app import webapp, memcache
from flask import json
import os


@webapp.route('/')
def main():
    return render_template("main.html")

@webapp.route('/get',methods=['POST'])
def get():
    key = request.form.get('key')

    if key in memcache:
        value = memcache[key]
        response = webapp.response_class(
            response=json.dumps(value),
            status=200,
            mimetype='application/json'
        )
    else:
        response = webapp.response_class(
            response=json.dumps("Unknown key"),
            status=400,
            mimetype='application/json'
        )

    return response

@webapp.route('/put',methods=['POST'])
def put():
    key = request.form.get('key')
    value = request.form.get('value')
    memcache[key] = value

    response = webapp.response_class(
        response=json.dumps("OK"),
        status=200,
        mimetype='application/json'
    )

    return response

@webapp.route('/UploadImage', methods=['POST'])
def UploadImage():
    image = request.files['image']

    base_path = os.path.dirname(__file__)    # current file path
    upload_path = os.path.join(base_path, 'static/images', image.filename)  # save file to path

    image.save(upload_path)
    return "OK"

