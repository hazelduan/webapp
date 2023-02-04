import mysql.connector
import sys
sys.path.append("..")
sys.path.append("..")
from database import database_credential
from configuration import base_path, file_system_path, backend_base_url


from flask import render_template, url_for, request, flash, redirect
from app import webapp
from flask import json
import requests
import os
from app import db, Images
from pathlib import Path

@webapp.route('/')
def main():
    return render_template("index.html")

@webapp.route('/upload_image')
def upload_image():
    return render_template("upload_image.html")

@webapp.route('/api/upload', methods=['POST'])
def UploadImage():
    
    image_key = request.form['key']
    image = request.files['file']
    
    save_directory = os.path.join(file_system_path, image_key)
    if not os.path.exists(save_directory):        # if dirs do not exist, create one
        os.makedirs(save_directory)

    save_path = os.path.join(save_directory, image.filename)  # image save path
    relative_path = os.path.join(image_key, image.filename)

    ##if image_key in database:
    #     ## update key in database
    db_image = Images.query.filter_by(image_key=image_key).first()
    if db_image == None:
        # Save the image_key and image path in database
        db_image = Images(image_key=image_key, image_path=relative_path)
        db.session.add(db_image)
        db.session.commit()
    else:
        # db already stored path
        os.remove(save_path)                        # delete the old image
        db_image.image_path = relative_path
        db.session.commit()
    print('save_path:', save_path)
    image.save(save_path)                  # save the image in local file system


    response = requests.get(backend_base_url + "/put", data={'image_key': image_key, 'image_path': relative_path})
    jsonResponse = response.json()
    answer = jsonResponse['success']

    response = webapp.response_class(
            response=json.dumps('success {}'.format(answer)),
            status=200,
            mimetype='application/json'
        )

    return response


@webapp.route('/image_lookup', methods=['POST','GET'])
def ImageLookup():

    if request.method == 'POST':
        image_key = request.form['image_key']

        response = requests.post(backend_base_url + "/get", data={'image_key': image_key})
        jsonResponse = response.json()
        image_content = jsonResponse['image_content']
        
        if image_content != 'not found':
            return render_template("display_image_from_cache.html", image_content=image_content, image_key=image_key)
        else:
            ## Interact with database
            db_image = Images.query.filter_by(image_key=image_key).first()
            if db_image != None:
                
                html_path = os.path.join('file_storage', db_image.image_path)

                
                # put the key into memcache
                #requests.get(backend_base_url + '/put', data={'image_key': image_key, 'image_path':db_image.image_path})
                return render_template("display_image.html", image_path=html_path, image_key=image_key)

            return "Image not found"
    return render_template('display_image.html')


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
        saved_path = os.path.join(file_system_path, db_image.image)
        os.remove(saved_path)
        ## Delete from database 
        db.session.delete(db_image)
    db.session.commit()

    ## Delete from memcache

    response = requests.get(backend_base_url + '/cache_clear')
    jsonResponse = response.json()
    return {'success':jsonResponse['success']}


@webapp.route('/memcache_option', methods=['GET', 'POST'])
def MemcacheOption():
    
    if request.method == 'POST':
        capacity = request.form['capacity']
        policy = request.form['policy']
        response = requests.get(backend_base_url + "/memcache_option", data={'capacity': capacity, 'policy':policy, 'method':'post'})
        jsonResponse = response.json()

    else:
        response = requests.get(backend_base_url + "/memcache_option", data={'capacity': '1', 'policy': '1', 'method':'get'})
        jsonResponse = response.json()
    
    replace_policy = jsonResponse['policy']
    memcache = jsonResponse['memcache']
    return render_template('memcache_option.html', 
                            memcache=memcache,
                            replace_policy=replace_policy
    )

@webapp.route('/cache_clear', methods=['POST'])
def CacheClear():
    response = requests.get(backend_base_url + '/cache_clear')
    jsonResponse = response.json()
    return {'success' : jsonResponse['success']}


@webapp.route('/memcache_statistics', methods=['GET'])
def MemStatistics():
    # url = "http://127.0.0.1:5001"

    # response = requests.get(url + '/statistics')
    # jsonResponse = response.json()

    # number_of_items = jsonResponse['number_of_items']
    # total_size = jsonResponse['total_size']
    mydb = mysql.connector.connect(
        host=database_credential.db_host,
        user=database_credential.db_user,
        passwd=database_credential.db_password,
    )
    my_cursor = mydb.cursor()
    my_cursor.execute(("USE IMAGES;"))
    # my_cursor.execute(("SELECT * FROM MEMCACHE_STATISTICS"))
    my_cursor.execute(("SELECT * FROM images.memcache_statistics ORDER BY id DESC LIMIT 120"))
    
    time = []
    number_of_items = []
    total_size_of_items = []
    number_of_request_served = []
    miss_rate = []
    hit_rate = []
    print(my_cursor)
    counter = 0
    for db_statis in my_cursor:
        time.append(str(db_statis[1]))
        number_of_items.append(db_statis[2])
        total_size_of_items.append(db_statis[3])
        number_of_request_served.append(db_statis[4])
        miss_rate.append(db_statis[5])
        hit_rate.append(db_statis[6])
        counter += 1
    print(type(time[2]))
    print(time[0])

    data_to_render = {'number_of_rows': counter, 'time':time, 'num_of_items':number_of_items, 'total_size_of_items':total_size_of_items, 'number_of_request_served':number_of_request_served, 'miss_rate':miss_rate, 'hit_rate':hit_rate}
    # return render_template('mem_statistics.html', number_of_rows = counter, time = time, num_of_items=number_of_items,
    #                                             total_size_of_items=total_size_of_items,
    #                                             number_of_request_served=number_of_request_served,
    #                                             miss_rate=miss_rate,
    #                                             hit_rate=hit_rate)
    return render_template('mem_statistics.html', data_to_render = data_to_render)

