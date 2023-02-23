from flask import render_template, url_for, request
from app import memapp, memcache, scheduler
from flask import json
from app import db, MemcacheConfig, MemcacheStatistics
import datetime
import sys
import os
import logging
import base64
sys.path.append("..")
sys.path.append("..")
from configuration import base_path, file_system_path, backend_base_url
import datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)

@memapp.route('/')
def main():
    html = '''
        <!DOCTYPE html>
            <html>
                <head>
                    <title>memcache index</title>
                </head>
                <body>
                    <h1><i>memcache index</i></h1>
                    <form action='/display_keys' method='get'>
                        <input type='submit' value='display keys'>
                    </form>
                </body>
            </html>
        '''
    return html


@memapp.route('/put',methods=['GET'])
def put():
    image_key = request.form.get('image_key')
    image_content = request.form.get('image_content')
    memcache.requests_num += 1

    if image_key in memcache.keys():
        memcache.pop(image_key)       # invalidate the key in memcache to update key-value
    
    memcache[image_key] = str.encode(image_content)
    
    response = {
        "success" : "true",
        "key" : image_key
    }
    return response

@memapp.route('/get',methods=['GET'])
def get():
    image_key = request.form.get('image_key')
    memcache.requests_num += 1
    memcache.cache_lookup += 1

    if image_key in memcache:
        image_content = memcache[image_key]
        decoded_image = image_content.decode()
        memcache.cache_hit +=1
        return {'image_content': decoded_image}
    
    memcache.cache_miss += 1
    return {'image_content': 'not found'}


@memapp.route('/memcache_option',methods=['GET', 'POST'])
def MemcacheOption():
    mem_config = MemcacheConfig.query.first()

    capacity = request.form['capacity']
    policy = request.form['policy']
    method = request.form['method']
    if method == 'post':
        mem_config.memsize = capacity
        mem_config.policy = policy
        db.session.commit()
        memcache.set_config(cache_size=int(capacity), policy=policy)
    return {'capacity': mem_config.memsize, 'policy': mem_config.policy, 'memcache': [key for key in memcache.keys()]}

@memapp.route('/cache_clear',methods=['GET'])
def CacheClear():
    memcache.clear()
    memcache.cur_size = 0
    return {'success' : 'true'}


@memapp.route('/key_invalidate', methods=['GET'])
def InvalidateKey():
    image_key = request.form['image_key']
    if image_key in memcache.keys():
        memcache.pop(image_key)


@memapp.route('/display_keys', methods=['GET'])
def DisplayKeys():
    return render_template('display_keys.html', memcache=memcache)

@memapp.route('/statistics', methods=['GET'])
def Statistics():
    number_of_items = len(memcache.keys())
    # total_size = len(memcache)
    total_size = memcache.cur_size

    request_num = memcache.requests_num

    if memcache.cache_lookup == 0:
        miss_rate = 0
        hit_rate = 0
    else:
        miss_rate = memcache.cache_miss / memcache.cache_lookup
        hit_rate = memcache.cache_hit / memcache.cache_lookup
    
    # provide current time to mysql time format
    cur_time = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-5]

    #store statics in database every 5 seconds
    store_statistics_in_database(cur_time, number_of_items, total_size, request_num, miss_rate, hit_rate)
    return {'store in database': 'true'}

def store_statistics_in_database(cur_time, number_of_items, total_size, request_num, miss_rate, hit_rate) -> None:
    with memapp.app_context():
        mem_statistics = MemcacheStatistics()
        mem_statistics.time = cur_time
        mem_statistics.num_of_items = number_of_items
        mem_statistics.total_size_of_items = total_size
        mem_statistics.number_of_requests_served  = request_num
        mem_statistics.miss_rate = miss_rate
        mem_statistics.hit_rate = hit_rate
        db.session.add(mem_statistics)
        db.session.commit()

# scheduler to store statistics in database
scheduler.add_job(func=Statistics, trigger='interval', seconds=5, id='job1')
# scheduler.start()


