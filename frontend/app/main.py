import mysql.connector
import sys
import logging

sys.path.append("..")
sys.path.append("..")
from database import database_credential
from configuration import base_path, file_system_path, backend_base_url, base_port, manager_port

from flask import render_template, url_for, request, flash, redirect
from app import webapp, cw_api, statistics, scheduler
from flask import json
import requests
import os
from app import db, Images, BUCKET_NAME, s3, s3_resource
from pathlib import Path
import base64
import hashlib
import signal
import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def signal_handler(sig, frame):
    print('You pressed ctrl+c !')
    StopScheduler()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
active_node = 8 #by default active node is 8
def get_active_node():
    active_node_response = requests.get(backend_base_url + str(manager_port) + '/get')
    jsonNodeResponse = active_node_response.json()
    active_node = jsonNodeResponse['active_node']
    return active_node

@webapp.route('/')
def main():

    active_node = get_active_node()
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
    active_node = get_active_node()
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
        active_node = get_active_node()
        print('the active node is:' + str(active_node))
        mem_port = mem_partition % active_node + base_port

        response = requests.get(backend_base_url + str(mem_port) + "/get", data={'image_key': image_key})
        jsonResponse = response.json()
        image_content = jsonResponse['image_content']
        statistics.add('lookup_num', 1)
        statistics.add('request_num', 1)
        if jsonResponse['cache_hit'] == 'true':
            statistics.add('hit_num', 1)
        else:
            statistics.add('miss_num', 1)
        if image_content != 'not found':
            print("Look up through memcache port" + str(mem_port))
            return render_template("display_image.html", image_content=image_content, image_key=image_key)
        else:
            ## Interact with database
            logging.info("------------------------------------")
            logging.info("Look up through file system")
            logging.info("------------------------------------")
            db_image = Images.query.filter_by(image_key=image_key).first()
            if db_image != None:
                logging.info("------------------------------------")
                logging.info("db finding ")
                logging.info("------------------------------------")
                obj = s3.get_object(Bucket=BUCKET_NAME, Key=db_image.image_path)
                image_content = base64.b64encode(obj['Body'].read()).decode()
                # put the key into memcache
                requests.post(backend_base_url + str(mem_port) + '/put', data={'image_key': image_key, 'image_content':image_content})
                statistics.add('request_num', 1)
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
    active_node = get_active_node()
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
    active_node = get_active_node()
    for i in range(active_node):
        response = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')

    jsonResponse = response.json()
    return {'success': jsonResponse['success']}


@webapp.route('/cache_clear', methods=['POST'])
def CacheClear():
    active_node = get_active_node()
    for i in range(active_node):
        response = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')
    jsonResponse = response.json()
    return {'success': jsonResponse['success']}

@webapp.route('/stop_scheduler', methods=['GET'])
def StopScheduler():
    # retrieve from manager app
    active_node = get_active_node()
    for mem_port in range(active_node):
        try:
            res = requests.get(backend_base_url + str(mem_port + base_port) + '/stop_scheduler')
        except requests.exceptions.ConnectionError:
            print(f'port {mem_port + base_port} offline')



@webapp.route('/api/configure_cache', methods=['POST'])
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
    # Set number of nodes
    response = requests.post(backend_base_url + str(manager_port) + '/resize',
                             data={'new_node_number': numNodes})
    # Set cache size and policy
    if policy == 'RR':
        translated_policy = 'Random'
    else:
        translated_policy = policy
    requests.post(backend_base_url + str(manager_port) + '/memcache_option',
                  data={'capacity': str(int(cacheSize) * 1024), 'policy': translated_policy})
    if expRatio != None and shrinkRatio != None and maxMiss != None and minMiss != None:
        # Set expRatio, shrinkRatio, maxMiss, and minMiss
        response = requests.post(backend_base_url + str(manager_port) + '/config_auto_scaler',
                                 data={'expandRatio': expRatio, 'shrinkRatio': shrinkRatio,
                                       'Max_Miss_Rate_threshold': float(maxMiss),
                                       'Min_Miss_Rate_threshold': float(minMiss)})
    resp = {"success": "true",
            "mode": mode,
            "numNodes": int(numNodes),
            "cacheSize": int(cacheSize),
            "policy": policy}
    response = webapp.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )
    return response


@webapp.route('/api/getNumNodes', methods=['POST'])
def Get_num_Nodes():
    node_response = requests.get(backend_base_url + str(manager_port) + '/get')
    json_node_response = node_response.json()
    num_active_nodes = json_node_response['active_node']
    resp = {"success": "true",
            "numNodes": num_active_nodes}
    response = webapp.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )
    return response

@webapp.route('/api/getRate', methods=['POST'])
def get_rate():
    rate_type = request.args.get('rate')
    if rate_type == 'miss':
        rate = 'miss'
    elif rate_type == 'hit':
        rate = 'hit'
    else:
        print('Invalid rate type')
    # getAverageMetric
    resp = {'success': 'true', 'rate': rate}
    response = webapp.response_class(
        response=json.dumps(resp),
        status=200,
        mimetype='application/json'
    )
    return response

@scheduler.task('interval', id='job_1', seconds=10)
@webapp.route("/pool_statistics", methods=['GET'])
def Statistics():
    # if statistics.data['request_num'] == 0:
    #     statistics.data['hit_rate'] = 0
    #     statistics.data['miss_rate'] = 0
    # else:
    #     statistics.data['hit_rate'] = statistics.data['hit_num'] / statistics.data['request_num']
    #     statistics.data['miss_rate'] = statistics.data['miss_num'] / statistics.data['request_num']
    statistics.add('node_num',get_active_node())
    for node in range(statistics.get('node_num')):
        try:
            res = requests.get(backend_base_url + str(node + base_port) + '/get_item_statistics')
            jsonResponse = res.json()
            statistics.add('item_num', int(jsonResponse['number_of_items']))
            statistics.add('total_size', float(jsonResponse['total_size']))
        except requests.exceptions.ConnectionError:
            print(f'port {node + base_port} offline')
    # provide current time to mysql time format
    #cur_time= datetime.datetime.now().strftime('%H:%M:%S.%f')[:-5]

    #store the statistics in cloudwatch
    store_statistics_in_cloudwatch(statistics.get_all())
    statistics.clear()


def store_statistics_in_cloudwatch(data):
    logging.info(str(data))
    cw_api.putMultipleMetric(data)
