import mysql.connector
import sys
import logging

sys.path.append("..")
sys.path.append("..")
from database import database_credential
from configuration import base_path, backend_base_url, frontend_port, base_port, auto_scaler_port, manager_port

from flask import render_template, url_for, request, flash, redirect
from api import manageapp
from flask import json
import requests
import os
from api import db, BUCKET_NAME, s3, s3_resource, cw_api
from pathlib import Path
import hashlib
import base64

import datetime

x = datetime.datetime.now()  # just for test

logger = logging.getLogger()
logger.setLevel(logging.INFO)

current_node_num = 8  # By default the node is 8.
mode = 'manual'  # By default the mode is manual.
policy = 'Random' # By default the policy is Random.
capacity = 1  # By default the capacity is 1.


@manageapp.route('/')
def main():
    return render_template("index.html")


@manageapp.route('/api/time')  # just for test (to connect react with python api)
def get_time():
    return {
        'Name': "hazel",
        "Date": x,
        "programming": "python"
    }


@manageapp.route('/memcache_option', methods=['GET', 'POST'])
def MemcacheOption():
    # should configure from manager app

    global current_node_num, capacity, policy
    active_node = current_node_num
    all_nodes_value_list = []

    if request.method == 'POST':
        capacity = request.form['capacity']
        if request.form['policy'] in ['Random', 'LRU']:
            policy = request.form['policy']
        for i in range(current_node_num):  # all nodes should have the same configuration.
            response = requests.get(backend_base_url + str(i + base_port) + "/memcache_option",
                                    data={'capacity': capacity, 'policy': policy, 'method': 'post'})
            print("current_node_num", current_node_num)
            print(i)
            print(response)
            jsonResponse = response.json()
            all_nodes_value_list.extend(jsonResponse['memcache'])
        # print("response of memoption: (post)" + str(jsonResponse))

    else:
        for i in range(current_node_num):
            response = requests.get(backend_base_url + str(i + base_port) + "/memcache_option",
                                    data={'capacity': '1', 'policy': '1', 'method': 'get'})
            jsonResponse = response.json()
            all_nodes_value_list.extend(jsonResponse['memcache'])
        # print("response of memoption: (get)" + str(jsonResponse))

    replace_policy = jsonResponse['policy']
    capacity = jsonResponse['capacity']
    capacity = str(int(int(capacity) / 1024))
    return render_template('memcache_option.html',
                           memcache=all_nodes_value_list,
                           replace_policy=replace_policy,
                           memsize=capacity
                           )


@manageapp.route('/cache_clear', methods=['POST'])
def CacheClear():
    for i in range(current_node_num):
        response = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')
    # print("Response of cache clear:" + response)
    jsonResponse = response.json()
    return {'success': jsonResponse['success']}


@manageapp.route('/memcache_statistics', methods=['GET'])
def MemStatistics():
    mydb = mysql.connector.connect(
        host=database_credential.db_host,
        user=database_credential.db_user,
        passwd=database_credential.db_password,
    )
    my_cursor = mydb.cursor()
    my_cursor.execute(("use {};".format(database_credential.db_name)))
    # my_cursor.execute(("SELECT * FROM MEMCACHE_STATISTICS"))
    my_cursor.execute(
        ("SELECT * FROM memcache_statistics ORDER BY id DESC LIMIT 30"))  # 30 min, each min is one counter.

    time = []
    number_of_items = []
    total_size_of_items = []
    number_of_request_served = []
    miss_rate = []
    hit_rate = []
    mem_nodes = []
    print(my_cursor)
    counter = 0
    for db_statis in my_cursor:
        time.append(str(db_statis[1]))
        number_of_items.append(db_statis[2])
        total_size_of_items.append(db_statis[3])
        number_of_request_served.append(db_statis[4])
        miss_rate.append(db_statis[5])
        hit_rate.append(db_statis[6])
        mem_nodes.append(db_statis[7])
        counter += 1
    # print(type(time[2]))
    # print(time[0])

    data_to_render = {'number_of_rows': counter,
                      'time': time,
                      'num_of_items': number_of_items,
                      'total_size_of_items': total_size_of_items,
                      'number_of_request_served': number_of_request_served,
                      'miss_rate': miss_rate,
                      'hit_rate': hit_rate,
                      'nodes': mem_nodes,
                      }
    return render_template('mem_statistics.html', data_to_render=data_to_render)


@manageapp.route('/resize', methods=['GET'])
def resize_page():
    return render_template('resize.html')


def resize_memcachePool(size):
    global current_node_num
    new_node_num = int(size)
    if new_node_num != current_node_num:  # reallocate the keys in memcache nodes
        # if new_node_num > current_node_num: #add new nodes
        #     for node in range(current_node_num, new_node_num):
        #         try:
        #             res = requests.get(backend_base_url + str(node + base_port) + '/start_scheduler')
        #         except requests.exceptions.ConnectionError:
        #             print("Can't connect to port " + str(node + base_port))

        # put_jsonResponse = {}
        for partition in range(16):
            if (partition % current_node_num) == (partition % new_node_num):
                print("Keys in this partition don't need to change node.")
                continue
            else:
                print("Keys in this partition need to change node.")
                # get the key from the old node and delete the key from old node
                response = requests.get(
                    backend_base_url + str(base_port + (partition % current_node_num)) + '/get_partition_images',
                    data={'partition': str(partition)})
                print("response of get_partition_images: " + str(response))
                jsonResponse = response.json()
                print("response of get_partition_images: " + str(jsonResponse))
                image_keys = jsonResponse['image_keys']
                images = jsonResponse['images']  # encoded image content
                # send the key to the new node
                put_response = requests.get(
                    backend_base_url + str(base_port + (partition % new_node_num)) + '/put_partition_images',
                    data={'images': images, 'image_keys': image_keys})
                put_jsonResponse = put_response.json()

        if put_jsonResponse['success'] == 'true':
            current_node_num = new_node_num

        logging.info("current_node_num : " + str(current_node_num))

    for node in range(current_node_num):
        try:
            res = requests.get(backend_base_url + str(node + base_port) + '/start_scheduler')
        except requests.exceptions.ConnectionError:
            print("Can't connect to port " + str(node + base_port))
    if current_node_num < 8:
        for node in range(current_node_num, 8, 1):
            try:
                res = requests.get(backend_base_url + str(node + base_port) + '/stop_scheduler')
            except requests.exceptions.ConnectionError:
                print("Can't connect to port " + str(node + base_port))
    return current_node_num


@manageapp.route('/resize', methods=['POST'])
def resize():
    new_node_num = request.form['new_node_number']
    resize_memcachePool(new_node_num)
    if int(new_node_num) != current_node_num:
        return {'success': 'false', "node_num": current_node_num}
    else:
        return {'success': 'true', "node_num": current_node_num}


@manageapp.route('/resize_manual', methods=['GET', 'POST'])
def ResizeMemcacheManual():
    # should configure from manager app
    global current_node_num, mode
    if request.method == 'POST':
        mode = 'manual'
        new_node_num = request.form['new_node_number']
        print(backend_base_url + str(manager_port) + url_for('resize'))
        requests.post(backend_base_url + str(manager_port) + url_for('resize'),
                      data={'new_node_number': new_node_num})
    return render_template('resize_manual.html',
                           current_node=current_node_num)

@manageapp.route("/config_auto_scaler", methods=['POST'])
def config_auto_scaler():
    global current_node_num
    Max_Miss_Rate_threshold = request.form['Max_Miss_Rate_threshold']
    if Max_Miss_Rate_threshold == '' or float(Max_Miss_Rate_threshold) < 0:
        return "Please enter valid number for Max_Miss_Rate_threshold"
    Min_Miss_Rate_threshold = request.form['Min_Miss_Rate_threshold']
    if Min_Miss_Rate_threshold == '' or float(Min_Miss_Rate_threshold) < 0:
        return "Please enter valid number for Min_Miss_Rate_threshold"
    expandRatio = request.form['expandRatio']
    if expandRatio == '' or float(expandRatio) < 0:
        return "Please enter valid number for expandRatio"
    shrinkRatio = request.form['shrinkRatio']
    if shrinkRatio == '' or float(shrinkRatio) < 0:
        return "Please enter valid number for shrinkRatio"
    response = requests.post(backend_base_url + str(auto_scaler_port) + '/update_params',
                             data={'active_node': current_node_num,
                                   'Max_Miss_Rate_threshold': Max_Miss_Rate_threshold,
                                   'Min_Miss_Rate_threshold': Min_Miss_Rate_threshold,
                                   'expandRatio': expandRatio,
                                   'shrinkRatio': shrinkRatio})
    if response.json()['success'] == 'true':
        return {'success': 'true', 'Max_Miss_Rate_threshold': Max_Miss_Rate_threshold,
                'Min_Miss_Rate_threshold': Min_Miss_Rate_threshold,
                'expandRatio': expandRatio,
                'shrinkRatio': shrinkRatio}
    else:
        return {'success': 'false'}


@manageapp.route('/resize_auto', methods=['GET', 'POST'])
def ResizeMemcacheAuto():
    # should configure from manager app
    global current_node_num, mode
    if request.method == 'POST':
        mode = 'auto'
        requests.post(backend_base_url + str(manager_port) + url_for('config_auto_scaler'),
                      data={'active_node': current_node_num,
                            'Max_Miss_Rate_threshold': request.form['Max_Miss_Rate_threshold'],
                            'Min_Miss_Rate_threshold': request.form['Min_Miss_Rate_threshold'],
                            'expandRatio': request.form['expandRatio'],
                            'shrinkRatio': request.form['shrinkRatio']})
    return render_template('resize_auto.html',
                           current_node=current_node_num)


@manageapp.route('/get', methods=['GET'])
def get():
    active_node = current_node_num

    return {'active_node': active_node}


@manageapp.route('/delete_all_application_data', methods=['GET'])
def DeleteAllData():
    # delete all data in memcache
    for i in range(current_node_num):
        response_memcache = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')
    jsonResponse = response_memcache.json()
    print(jsonResponse['success'])
    if jsonResponse['success'] == 'true':
        # delete all data in database
        mydb = mysql.connector.connect(
            host=database_credential.db_host,
            user=database_credential.db_user,
            passwd=database_credential.db_password,
        )
        my_cursor = mydb.cursor()
        my_cursor.execute(("use {};".format(database_credential.db_name)))
        my_cursor.execute(("DELETE FROM images"))
        mydb.commit()
        # if database is empty, delete all data in s3
        db_response = my_cursor.execute(("SELECT * FROM images"))
        print(db_response)
        if db_response == None:
            bucket = s3_resource.Bucket(BUCKET_NAME)
            bucket.objects.all().delete()
            return {'success': True}
        else:
            return {'db_clear': False}
    else:
        return {'cache_clear': False}


@manageapp.route('/set_mode', methods=['POST'])
def setMode():
    """
    Set the mode of the application to either 'auto' or 'manual'.
    """
    global mode
    incoming_mode = request.form['mode']
    if (incoming_mode not in ['auto', 'manual']):
        return {'success': False,
                'mode': mode}
    mode = incoming_mode
    print("mode: " + mode)
    return {'success': True,
            'mode': mode}
