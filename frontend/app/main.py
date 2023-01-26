
from flask import render_template, url_for, request, flash, redirect
from app import webapp, memcache
from flask import json
import os
import sys
sys.path.append('..')
sys.path.append('..')
from app import db, Images, MemcacheConfig

@webapp.route('/')
def main():
    # Initialize memcache config
    init_memconfig = MemcacheConfig.query.first()

    if init_memconfig == None:              # when the database is created initially
        init_memconfig = MemcacheConfig(policy='Random', memsize='10')
        db.session.add(init_memconfig)
        db.session.commit()
    
    return render_template("main.html")


@webapp.route('/api/upload', methods=['POST'])
def UploadImage():
    image_key = request.form['key']
    image = request.files['file']

    base_path = os.path.dirname(__file__)    # current file path
    save_path = os.path.join(base_path, 'static/images')
    if not os.path.exists(save_path):        # if dirs do not exist, create one
        os.makedirs(save_path)

    save_path = os.path.join(save_path, image.filename)  # image save path
    image_path = os.path.join('static/images', image.filename)


    if image_key in memcache.keys():
        memcache.pop(image_key)                         # invalidate the key in memcache

    # Save the image_key and image path in memcache
    memcache[image_key] = image_path


    ##if image_key in database:
    #     ## update key in database
    db_image = Images.query.filter_by(image_key=image_key).first()
    if db_image != None:
        old_save_path = os.path.join(base_path, db_image.image)
        os.remove(old_save_path)                        # delete the old image
        db_image.image = image_path
        db.session.commit()
    # Save the image_key and image path in database
    else:
        db_image = Images(image_key=image_key, image=image_path)
        db.session.add(db_image)
        db.session.commit()

    image.save(save_path)                  # save the image in local file system
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
    else:
        ## Interact with database
        db_image = Images.query.filter_by(image_key=image_key).first()
        if db_image != None:
            image_path = db_image.image
            return render_template("display_image.html", image_path=image_path, image_key=image_key)

        return "Image not found"


@webapp.route('/api/list_keys', methods=['POST'])
def KeysDisplay():
    ## Show all the available keys in database
    db_images = Images.query.all()
    return render_template('display_keys.html', db_images=db_images)


@webapp.route('/api/delete_all', methods=['POST'])
def DeleteAllKeys():
    
    ## Delete from local file system
    base_path = os.path.dirname(__file__)
    db_images = Images.query.all()
    for db_image in db_images:                ## Keys should be from database, for now we use memcache
        save_path = os.path.join(base_path, db_image.image)
        os.remove(save_path)
        ## Delete from database 
        db.session.delete(db_image)
    db.session.commit()

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
    mem_config = MemcacheConfig.query.first()
    if request.method == 'POST':
        capacity = request.form['capacity']
        policy = request.form['policy']
        mem_size = capacity
        replace_policy = policy
        
        mem_config.memsize = capacity
        mem_config.policy = policy
        db.session.commit()
    else:
        mem_size = mem_config.memsize       ## should be retrieved from database
        replace_policy = mem_config.policy
    
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

