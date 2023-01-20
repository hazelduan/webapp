
from flask import render_template, url_for, request, flash, redirect
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

@webapp.route('/api/upload', methods=['POST'])
def UploadImage():
    image_key = request.form['key']
    image = request.files['file']

    base_path = os.path.dirname(__file__)    # current file path
    save_path = os.path.join(base_path, 'static/images', image.filename)  # image save path
    image_path = os.path.join('static/images', image.filename)

    image.save(save_path)                  # save the image in local file system

    # Save the image_key and image path in memcache
    memcache[image_key] = image_path

    # Save the image_key and image path in database
    ##
    ##
    resp = {
        "success" : "true",
        "key" : image_key
    }
    response = webapp.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )

    return response

@webapp.route('/image_lookup', methods=['POST'])
def ImageLookup():
    image_key = request.form['image_key']

    if image_key in memcache:
        image_path = memcache[image_key]
        return render_template("display_image.html", image_path=image_path, image_key=image_key)
    # '''Interact with database
    # elif image_key in db:
    #    image_path = db[image_key]
    #    return render_template("display_image.html", image_path=image_path, image_key=image_key)
    # '''
    else:
        return "Image not found"

@webapp.route('/api/list_keys', methods=['POST'])
def KeysDisplay():
    ## Show all the available keys in database
    return render_template('display_keys.html')


@webapp.route('/api/delete_all', methods=['POST'])
def DeleteAllKeys():
    
    ## Delete from local file system
    base_path = os.path.dirname(__file__)
    for image_path in memcache.values():                ## Keys should be from database, for now we use memcache
        save_path = os.path.join(base_path, image_path)
        os.remove(save_path)

    ## Delete from memcache
    memcache.clear()

    resp = {"success" : "true"}
    response = webapp.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )
    return response


@webapp.route('/memcache_option', methods=['GET', 'POST'])
def MemcacheOption():
    if request.method == 'POST':
        capacity = request.form['capacity']
        policy = request.form['policy']
        mem_size = capacity
        replace_policy = policy
        ## should be update to database
        ##
        ## 
    else:
        mem_size = 10       ## should be retrieved from database
        replace_policy = "Random"
    return render_template('memcache_option.html', 
                            memcache=memcache,
                            mem_size=mem_size,
                            replace_policy=replace_policy
    )

@webapp.route('/cache_clear', methods=['POST'])
def CacheClear():
    memcache.clear()
    flash("Cache clear success!")
    return redirect(url_for('MemcacheOption'))

