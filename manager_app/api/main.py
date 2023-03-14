import mysql.connector
import sys
import logging

sys.path.append("..")
sys.path.append("..")
from database import database_credential
from configuration import backend_base_url, auto_scaler_port, manager_port, EC2_NODE_ID, EC2_CONTROL_ID, MODE, memcache_port

from flask import render_template, url_for, request, flash, redirect
from api import manageapp, scheduler
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
public_ips = []
local_public_ip = ''

if MODE == 'LOCAL':
    local_public_ip = backend_base_url
    for _ in range(8):
        public_ips.append(backend_base_url)

@manageapp.route('/')
def main():
    return render_template("index.html")


@manageapp.route('/update_public_ips', methods=['POST'])
def UpdatePublicIP():
    global public_ips
    if MODE == 'CLOUD':
        logging.info('receve pubic ips : ' + str(request.form['public_ips']))
        if len(public_ips) < 8:
            public_ips.append(request.form['public_ips'])
        logging.info("in backend, public ips " + str(public_ips))
    return {'success' : 'true'}


@manageapp.route('/update_local_ip', methods=['POST'])
def UpdateLocalIP():
    global local_public_ip
    if MODE == 'CLOUD':
        local_public_ip = request.form['local_public_ip']
        logging.info("Manage App Public ip " + local_public_ip)
    return {'success' : 'true'}


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
            response = requests.get(public_ips[i] + str(memcache_port[i]) + "/memcache_option", 
                                    data={'capacity': capacity, 'policy':policy, 'method':'post'})
            jsonResponse = response.json()
            all_nodes_value_list.extend(jsonResponse['memcache'])
        # print("response of memoption: (post)" + str(jsonResponse))

    else:
        for i in range(current_node_num):
            response = requests.get(public_ips[i] + str(memcache_port[i]) + "/memcache_option", 
                                    data={'capacity': '1', 'policy': '1', 'method':'get'})
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
        response = requests.get(public_ips[i] + str(memcache_port[i]) + '/cache_clear')
    #print("Response of cache clear:" + response)
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
        mem_nodes.append(db_statis[2])
        number_of_items.append(db_statis[3])
        total_size_of_items.append(db_statis[4])
        number_of_request_served.append(db_statis[5])
        miss_rate.append(db_statis[6])
        hit_rate.append(db_statis[7])

        counter += 1
    # print(type(time[2]))
    # print(time[0])

    data_to_render = {'number_of_rows': counter, 
                        'time':time, 
                        'num_of_items':number_of_items, 
                        'total_size_of_items':total_size_of_items, 
                        'number_of_request_served':number_of_request_served, 
                        'miss_rate':miss_rate, 
                        'hit_rate':hit_rate,
                        'nodes':mem_nodes,
                        }
    return render_template('mem_statistics.html', data_to_render = data_to_render)


@scheduler.task('interval', id='job_1', seconds=60)
def cw_statistics():
    # dict = {}
    # self.data = {
#             'node_num': 0,
#             'request_num': 0,
#             'hit_num': 0,
#             'miss_num': 0,
#             'lookup_num': 0,
#             'item_num': 0,
#             'total_size': 0.0,
#         }
    time_slice = 30 # s
    node_res = cw_api.getMetricData(time_slice, 'node_num', 'Average')
    request_res = cw_api.getMetricData(time_slice, 'request_num', 'Sum')
    lookup_res = cw_api.getMetricData(time_slice, 'lookup_num', 'Sum')
    item_res = cw_api.getMetricData(time_slice, 'item_num', 'Average')
    size_res = cw_api.getMetricData(time_slice, 'total_size', 'Average')

    logging.info("lookup_res: " + str(lookup_res))
    logging.info("node_num_res: " + str(node_res))

    def get_metric_res(res, label):
        if len(res['Datapoints']) > 0:
            return res['Datapoints'][0][label]
        
        return 0
    
    node_num = int(get_metric_res(node_res, 'Average'))
    request_num = get_metric_res(request_res, 'Sum')
    item_num = int(get_metric_res(item_res, 'Average'))
    total_size = get_metric_res(size_res, 'Average')
    cur_time = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-5]

    miss_rate = cw_api.getAverageMetric(time_slice,'miss_num', 'lookup_num')
    hit_rate = cw_api.getAverageMetric(time_slice, 'hit_num', 'lookup_num')

    mydb = mysql.connector.connect(
        host=database_credential.db_host,
        user=database_credential.db_user,
        passwd=database_credential.db_password,
    )
    my_cursor = mydb.cursor()
    my_cursor.execute(("use {};".format(database_credential.db_name)))
    sql_insert = f"INSERT INTO memcache_statistics (time, node_num, num_of_items, total_size_of_items, number_of_requests_served, miss_rate, hit_rate ) VALUES ('{cur_time}', {node_num}, {item_num}, {total_size}, {request_num}, {miss_rate}, {hit_rate})"
    logging.info("sql insert " + sql_insert)
    my_cursor.execute(sql_insert)#, (cur_time, node_num, item_num, total_size, request_num, miss_rate, hit_rate)))
    mydb.commit()

@manageapp.route('/resize', methods=['GET'])
def resize_page():
    return render_template('resize.html', mode=mode)


def resize_memcachePool(size):
    global current_node_num
    new_node_num = size
    if new_node_num != current_node_num:  # reallocate the keys in memcache nodes
        for partition in range(16):
            if (partition % current_node_num) == (partition % new_node_num):
                print("Keys in this partition don't need to change node.")
                continue
            else:
                print("Keys in this partition need to change node.")
                # get the key from the old node and delete the key from old node
                response = requests.get(
                    public_ips[(partition % current_node_num)] + str(memcache_port[partition % current_node_num]) + '/get_partition_images',
                    data={'partition': str(partition)})
                jsonResponse = response.json()
                image_keys = jsonResponse['image_keys']
                print('keys fetch from memcache to manager app', image_keys)
                images = jsonResponse['images']  # encoded image content
                # send the key to the new node
                put_response = requests.get(
                    public_ips[(partition % current_node_num)] + str(memcache_port[partition % current_node_num]) + '/put_partition_images',
                    data={'images': images, 'image_keys': image_keys})
                put_jsonResponse = put_response.json()

        if put_jsonResponse['success'] == 'true':
            current_node_num = new_node_num

        logging.info("current_node_num : " + str(current_node_num))

    return current_node_num


@manageapp.route('/resize', methods=['POST'])
def resize():
    new_node_num = int(request.form['new_node_number'])
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
        requests.post(local_public_ip + str(manager_port) + url_for('set_mode'), data={'mode': 'manual'})
        new_node_num = request.form['new_node_number']
        # print(local_public_ip + str(manager_port) + url_for('resize'))
        requests.post(local_public_ip + str(manager_port) + url_for('resize'),
                      data={'new_node_number': str(new_node_num)})
        logging.info("current_node_num : " + str(current_node_num))
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
    response = requests.post(local_public_ip + str(auto_scaler_port) + '/update_params',
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
        requests.post(local_public_ip + str(manager_port) + url_for('set_mode'), data={'mode': 'auto'})
        requests.post(local_public_ip + str(manager_port) + url_for('config_auto_scaler'),
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
        response_memcache = requests.get(public_ips[i] + str(memcache_port[i]) + '/cache_clear')
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

@manageapp.route('/get_mode', methods=['GET'])
def get_mode():
    """
    Get the mode of the application.
    """
    global mode
    return {'success': True,
            'mode': mode}


@manageapp.route('/set_mode', methods=['POST'])
def set_mode():
    """
    Set the mode of the application to either 'auto' or 'manual'.
    """
    global mode
    incoming_mode = request.form['mode']
    if incoming_mode not in ['auto', 'manual']:
        return {'success': False,
                'mode': mode}
    mode = incoming_mode
    if mode == 'auto':
        requests.post(local_public_ip + str(auto_scaler_port) + '/turn_on_auto_scaler')
    elif mode == 'manual':
        requests.post(local_public_ip + str(auto_scaler_port) + '/turn_off_auto_scaler')
    else:
        print("Invalid mode: " + mode)
    print("set mode to : " + mode)
    return {'success': True,
            'mode': mode}
