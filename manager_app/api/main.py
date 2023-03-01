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

import datetime
x = datetime.datetime.now() #just for test


logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
    print("Response of cache clear:" + response)
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
