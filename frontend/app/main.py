import mysql.connector
import sys
import logging

sys.path.append("..")
sys.path.append("..")
from database import database_credential
from configuration import base_path, file_system_path, backend_base_url, base_port, manager_port

from flask import render_template, url_for, request, flash, redirect
from app import webapp
from flask import json
import requests
import os
from app import db, Images, BUCKET_NAME, s3, s3_resource
from pathlib import Path
import base64
import hashlib
import signal

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def signal_handler(sig, frame):
    print('You pressed ctrl+c !')
    StopScheduler()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

active_node = 8


@webapp.route('/')
def main():
    return render_template("index.html", active_node=active_node)


@webapp.route('/upload_image')
def upload_image():
    return render_template("upload_image.html")


@webapp.route('/api/upload', methods=['POST'])
def UploadImage():
    image_key = request.form['key']
    image = request.files['file']

    if image_key == '' or image.filename == "":
        return "please enter key and upload file"

    save_path = image_key + '/' + image.filename

    ##if image_key in database:
    #     ## update key in database
    db_image = Images.query.filter_by(image_key=image_key).first()
    if db_image == None:
        # Save the image_key and image path in database
        db_image = Images(image_key=image_key, image_path=save_path)
        db.session.add(db_image)
        db.session.commit()
    else:
        # db already stored path
        delete_path = os.path.join(file_system_path, db_image.image_path)
        if os.path.exists(delete_path):
            os.remove(delete_path)  # delete the old image
        db_image.image_path = save_path
        db.session.commit()
    print("image type is : ", type(image))
    print("image is : ", image)

    encoded_image = base64.b64encode(image.read())
    image_content = encoded_image.decode();
    image.seek(0)  # reset the file pointer to the beginning of the file.
    s3.upload_fileobj(image, BUCKET_NAME, save_path)  # After uploading, the image will be closed.
    print('the type of image_content is:', type(image_content))

    # MD5 Hash Calculation
    image_key_md5 = hashlib.md5(image_key.encode('utf-8')).hexdigest()
    mem_partition = int(image_key_md5[0], 16)  # from hex string to deci int
    # number of active node should be retrieve from manage app
    # requests.get(url_for_manage_app, ..)
    active_node_response = requests.get(backend_base_url + str(manager_port) + '/get')
    jsonNodeResponse = active_node_response.json()
    active_node = jsonNodeResponse['active_node']
    print('the active node is:' + str(active_node))
    mem_port = mem_partition % active_node + base_port
    response = requests.post(backend_base_url + str(mem_port) + "/put",
                             data={'image_key': image_key, 'image_content': image_content})
    print('the response is:', response)
    jsonResponse = response.json()

    resp = {"success": jsonResponse['success'],
            "key": image_key}
    response = webapp.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )

    return response


@webapp.route('/image_lookup', methods=['POST', 'GET'])
def ImageLookup():
    if request.method == 'POST':
        image_key = request.form['image_key']

        # MD5 Calculation
        image_key_md5 = hashlib.md5(image_key.encode('utf-8')).hexdigest()
        mem_partition = int(image_key_md5[0], 16)  # from hex string to deci int
        # number of active node should be retrieve from manage app
        # requests.get(url_for_manage_app, ..)
        active_node_response = requests.get(backend_base_url + str(manager_port) + '/get')
        jsonNodeResponse = active_node_response.json()
        active_node = jsonNodeResponse['active_node']
        print('the active node is:' + str(active_node))
        mem_port = mem_partition % active_node + base_port

        response = requests.get(backend_base_url + str(mem_port) + "/get", data={'image_key': image_key})
        jsonResponse = response.json()
        image_content = jsonResponse['image_content']

        if image_content != 'not found':
            print("Look up through memcache port" + str(mem_port))
            return render_template("display_image.html", image_content=image_content, image_key=image_key)
        else:
            ## Interact with database
            print("Look up through file system")
            db_image = Images.query.filter_by(image_key=image_key).first()
            if db_image != None:
                obj = s3.get_object(Bucket=BUCKET_NAME, Key=db_image.image_path)
                image_content = base64.b64encode(obj['Body'].read()).decode()
                # put the key into memcache
                requests.get(backend_base_url + str(mem_port) + '/put',
                             data={'image_key': image_key, 'image_content': image_content})
                return render_template("display_image.html", image_content=image_content, image_key=image_key)
            return "Image not found"
    return render_template('display_image.html')


@webapp.route('/api/key/<key_value>', methods=['POST'])
def ImageLookupForTest(key_value):
    image_key = key_value

    # MD5 Calculation
    image_key_md5 = hashlib.md5(image_key.encode('utf-8')).hexdigest()
    mem_partition = int(image_key_md5[0], 16)  # from hex string to deci int
    # number of active node should be retrieve from manage app
    # requests.get(url_for_manage_app, ..)
    active_node_response = requests.get(backend_base_url + str(manager_port) + '/get')
    jsonNodeResponse = active_node_response.json()
    active_node = jsonNodeResponse['active_node']
    print('the active node is:' + str(active_node))
    mem_port = mem_partition % active_node + base_port

    response = requests.get(backend_base_url + str(mem_port) + "/get", data={'image_key': image_key})
    jsonResponse = response.json()
    image_content = jsonResponse['image_content']

    if image_content == 'not found':
        db_image = Images.query.filter_by(image_key=image_key).first()
        if db_image != None:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=db_image.image_path)
            image_content = base64.b64encode(obj['Body'].read()).decode()
            # put the key into memcache
            requests.get(backend_base_url + str(mem_port) + '/put',
                         data={'image_key': image_key, 'image_content': image_content})
            resp = {
                "success": "true",
                "key": image_key,
                "content": image_content
            }
        else:
            resp = {
                "success": "false",
                "error": {
                    "code": "404",
                    "message": "image not found"
                }
            }
    else:
        # found the image in cache
        resp = {
            "success": "true",
            "key": image_key,
            "content": image_content
        }
    return resp


@webapp.route('/api/list_keys_True')
def KeysDisplay():
    ## Show all the available keys in database
    db_images = Images.query.all()
    return render_template('display_keys.html', db_images=db_images)


@webapp.route('/api/list_keys', methods=['POST'])
def KeysDisplayForTest():
    db_images = Images.query.all()
    keys_array = [db_image.image_key for db_image in db_images]
    resp = {
        "success": "true",
        "keys": keys_array
    }

    return resp


@webapp.route('/api/delete_all', methods=['POST'])
def DeleteAllKeys():
    ## Delete all from s3 bucket

    bucket = s3_resource.Bucket(BUCKET_NAME)
    bucket.objects.all().delete()

    ## Delete from database
    db_images = Images.query.all()
    for db_image in db_images:  ## Keys should be from database, for now we use memcache
        # Design choice: Can delete the file in s3 bucket one by one here, but we delete all already.
        db.session.delete(db_image)
    db.session.commit()

    ## Delete from all the memcache
    active_node_response = requests.get(backend_base_url + str(manager_port) + '/get')
    jsonNodeResponse = active_node_response.json()
    active_node = jsonNodeResponse['active_node']
    for i in range(active_node):
        response = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')

    jsonResponse = response.json()
    return {'success': jsonResponse['success']}


# @webapp.route('/memcache_option', methods=['GET', 'POST'])
# def MemcacheOption():
#     # should configure from manager app, temporarily won't delete it as a backup
#     if request.method == 'POST':
#         capacity = request.form['capacity']
#         policy = request.form['policy']
#         response = requests.get(backend_base_url + "/memcache_option", data={'capacity': capacity, 'policy':policy, 'method':'post'})
#         jsonResponse = response.json()

#     else:
#         response = requests.get(backend_base_url + "/memcache_option", data={'capacity': '1', 'policy': '1', 'method':'get'})
#         jsonResponse = response.json()

#     replace_policy = jsonResponse['policy']
#     memcache_values = jsonResponse['memcache']
#     capacity = jsonResponse['capacity']
#     capacity = str(int(int(capacity) / 1024))
#     return render_template('memcache_option.html', 
#                             memcache=memcache_values,
#                             replace_policy=replace_policy,
#                             memsize = capacity
#     )

@webapp.route('/cache_clear', methods=['POST'])
def CacheClear():
    active_node = 8
    for i in range(active_node):
        response = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')
    jsonResponse = response.json()
    return {'success': jsonResponse['success']}


# @webapp.route('/memcache_statistics', methods=['GET'])
# def MemStatistics():

#     mydb = mysql.connector.connect(
#         host=database_credential.db_host,
#         user=database_credential.db_user,
#         passwd=database_credential.db_password,
#     )
#     my_cursor = mydb.cursor()
#     my_cursor.execute(("USE {};".format(database_credential.db_name)))
#     my_cursor.execute(("SELECT * FROM memcache_statistics ORDER BY id DESC LIMIT 30;"))

#     time = []
#     number_of_items = []
#     total_size_of_items = []
#     number_of_request_served = []
#     miss_rate = []
#     hit_rate = []
#     mem_nodes = []
#     print(my_cursor)
#     counter = 0
#     for db_statis in my_cursor:
#         time.append(str(db_statis[1]))
#         number_of_items.append(db_statis[2])
#         total_size_of_items.append(db_statis[3])
#         number_of_request_served.append(db_statis[4])
#         miss_rate.append(db_statis[5])
#         hit_rate.append(db_statis[6])
#         mem_nodes.append(db_statis[7])
#         counter += 1
#     print(type(time[2]))
#     print(time[0])

#     data_to_render = {'number_of_rows': counter, 
#                         'time':time, 
#                         'num_of_items':number_of_items, 
#                         'total_size_of_items':total_size_of_items, 
#                         'number_of_request_served':number_of_request_served, 
#                         'miss_rate':miss_rate, 
#                         'hit_rate':hit_rate,
#                         'nodes':mem_nodes}
#     return render_template('mem_statistics.html', data_to_render = data_to_render)

@webapp.route('/stop_scheduler', methods=['GET'])
def StopScheduler():
    # retrieve from manager app
    active_node_response = requests.get(backend_base_url + str(manager_port) + '/get')
    jsonNodeResponse = active_node_response.json()
    active_node = jsonNodeResponse['active_node']
    for mem_port in range(active_node):
        try:
            res = requests.get(backend_base_url + str(mem_port + base_port) + '/stop_scheduler')
        except requests.exceptions.ConnectionError:
            print(f'port {mem_port + base_port} offline')


@webapp.route("/update_node", methods=['POST'])
def UpdateNode():
    global active_node
    active_node = int(request.form['active_node'])

    return redirect(url_for('main'))


# @webapp.route("/delete_ec2", methods=['GET'])
# def DeleteEC2():
#     instances = ec2.instances.all()

#     for instance in instances:
#         ec2.instances.filter(InstanceIds=[instance.id]).terminate()
#     return 'delete success!'

@webapp.route("/api/configure_cache", methods=['POST'])
def ConfigureCache():
    mode = request.args.get('mode')
    numNodes = request.args.get('numNodes')
    cacheSize = request.args.get('cacheSize')
    policy = request.args.get('policy')
    expRatio = request.args.get('expRatio')
    shrinkRatio = request.args.get('shrinkRatio')
    maxMiss = request.args.get('maxMiss')
    minMiss = request.args.get('minMiss')

    # Set mode
    response = requests.post(backend_base_url + str(manager_port) + '/set_mode',
                             data={'mode': mode})
    print(response.json())
    # Set number of nodes
    response = requests.post(backend_base_url + str(manager_port) + '/resize',
                             data={'new_node_number': numNodes})
    print(response.json())
    # Set cache size and policy
    if policy == 'RR':
        policy == 'Random'
    requests.post(backend_base_url + str(manager_port) + '/memcache_option',
                  data={'capacity': cacheSize, 'policy': policy})

    # Set expRatio, shrinkRatio, maxMiss, and minMiss
    response = requests.post(backend_base_url + str(manager_port) + '/config_auto_scaler',
                             data={'expandRatio': expRatio, 'shrinkRatio': shrinkRatio,
                                   'Max_Miss_Rate_threshold': float(maxMiss),
                                   'Min_Miss_Rate_threshold': float(minMiss)})
    print(response)

    print(mode)
    print(numNodes)
    print(cacheSize)
    print(policy)
    print(expRatio)
    print(shrinkRatio)
    print(maxMiss)
    print(minMiss)

    resp = {"success": "true",
            "mode": mode,
            "numNodes": int(numNodes),
            "cacheSize": int(cacheSize),
            "policy": policy}
    print(resp)
    response = webapp.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )
    return response


@webapp.route("/api/getNumNodes", methods=['POST'])
def GetNumNodes():
    nodeResponse = requests.get(backend_base_url + str(manager_port) + '/get')
    jsonNodeResponse = nodeResponse.json()
    numActiveNodes = jsonNodeResponse['active_node']
    resp = {"success": "true",
            "numNodes": numActiveNodes}
    response = webapp.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )
    return response
