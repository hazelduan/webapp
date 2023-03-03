import mysql.connector
import sys
import logging
sys.path.append("..")
sys.path.append("..")
from database import database_credential
from configuration import base_path, backend_base_url, base_port


from flask import render_template, url_for, request, flash, redirect
from api import manageapp
from flask import json
import requests
import os
from api import db, BUCKET_NAME, s3, s3_resource
from pathlib import Path
import hashlib
import base64

import datetime
x = datetime.datetime.now() #just for test


logger = logging.getLogger()
logger.setLevel(logging.INFO)

current_node_num = 8# By default the node is 8.

@manageapp.route('/')
def main():
    return render_template("index.html")

@manageapp.route('/api/time')#just for test (to connect react with python api)
def get_time():
    return {
        'Name':"hazel", 
        "Date":x, 
        "programming":"python"
        }

@manageapp.route('/memcache_option', methods=['GET', 'POST'])
def MemcacheOption():
    # should configure from manager app
    active_node = 8
    if request.method == 'POST':
        capacity = request.form['capacity']
        policy = request.form['policy']
        for i in range(active_node):#all nodes should have the same comfiguration.
            response = requests.get(backend_base_url + str(i + base_port) + "/memcache_option", data={'capacity': capacity, 'policy':policy, 'method':'post'})
        jsonResponse = response.json()
        #print("response of memoption: (post)" + str(jsonResponse))

    else:
        for i in range(active_node):
            response = requests.get(backend_base_url + str(i + base_port) + "/memcache_option", data={'capacity': '1', 'policy': '1', 'method':'get'})
        jsonResponse = response.json()
        #print("response of memoption: (get)" + str(jsonResponse))
    
    replace_policy = jsonResponse['policy']
    memcache_values = jsonResponse['memcache']
    capacity = jsonResponse['capacity']
    capacity = str(int(int(capacity) / 1024))
    return render_template('memcache_option.html', 
                            memcache=memcache_values,
                            replace_policy=replace_policy,
                            memsize = capacity
    )

@manageapp.route('/cache_clear', methods=['POST'])
def CacheClear():
    active_node = 8
    for i in range(active_node):
        response = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')
    #print("Response of cache clear:" + response)
    jsonResponse = response.json()
    return {'success' : jsonResponse['success']}


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
    my_cursor.execute(("SELECT * FROM memcache_statistics ORDER BY id DESC LIMIT 30"))# 30 min, each min is one counter.

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
    print(type(time[2]))
    print(time[0])

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


@manageapp.route('/resize', methods=['GET', 'POST'])
def ResizeMemcachePool():
    if 'Manual Resize' in request.form:
        return redirect(url_for('ResizeMemcacheManual'))
    elif 'Auto Resize' in request.form:
        return redirect(url_for('ResizeMemcacheAuto'))

@manageapp.route('/resize_manual', methods=['GET', 'POST'])
def ResizeMemcacheManual():
    # should configure from manager app
    global current_node_num
    max_node = 8
    if request.method == 'POST':
        new_node_num = request.form['new_node_number']
        if new_node_num != current_node_num:
            for i in range(max_node):
                response = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')
            jsonResponse = response.json()
            if jsonResponse['success'] == True:
                current_node_num = new_node_num

                mydb = mysql.connector.connect(
                    host=database_credential.db_host,
                    user=database_credential.db_user,
                    passwd=database_credential.db_password,
                )
                my_cursor = mydb.cursor()
                my_cursor.execute(("use {};".format(database_credential.db_name)))
                my_cursor.execute(("SELECT * FROM images ORDER BY id")) #fetch image keys from database
                for db_image in my_cursor:
                    image_key = db_image[1]
                    image_key_md5 = hashlib.md5(image_key.encode('utf-8')).hexdigest()
                    mem_partition = int(image_key_md5[0], 16)       # from hex string to deci int
                    mem_port = mem_partition % current_node_num + base_port # get the port number of the key again
                    obj = s3.get_object(Bucket=BUCKET_NAME, Key=image_key)
                    image_content = base64.b64encode(obj['Body'].read()).decode()# get the image content from s3
                    # put the key into memcache and store the images into the memcache again
                    requests.get(backend_base_url + str(mem_port) + '/put', data={'image_key': image_key, 'image_content':image_content})
    return render_template('resize.html', 
                            current_node = current_node_num,)

@manageapp.route('/resize_auto', methods=['GET','POST'])
def ResizeMemcacheAuto():
    # should configure from manager app
    global current_node_num
    max_node = 8
    if request.method == 'POST':
        Max_Miss_Rate_threshold = request.form['Max_Miss_Rate_threshold'] 
        Min_Miss_Rate_threshold = request.form['Min_Miss_Rate_threshold']
        expandRatio = request.form['expandRatio']
        shrinkRatio = request.form['shrinkRatio']
    return render_template('resize.html',
                            current_node = current_node_num,)

@manageapp.route('/delete_all_application_data', methods=['POST'])
def DeleteAllData():
    active_node = current_node_num
    # delete all data in memcache
    for i in range(active_node):
        response_memcache = requests.get(backend_base_url + str(i + base_port) + '/cache_clear')

    if response_memcache.json()['success'] == True:
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
        #if database is empty, delete all data in s3
        db_response = my_cursor.execute(("SELECT * FROM images"))
        if db_response == 'Empty set':
            bucket = s3_resource.Bucket(BUCKET_NAME)
            bucket.objects.all().delete()
            return {'success' : True}
        else:
            return {'db_clear' : False}
    else:
        return {'cache_clear' : False}
