import schedule
import time
from flask import render_template, url_for, request
from app import memapp, memcache
from flask import json

from app import db, MemcacheConfig, MemcacheStatistics

@memapp.route('/')
def main():
    # Initialize memcache config
    init_memconfig = MemcacheConfig.query.first()

    if init_memconfig == None:              # when the database is created initially
        init_memconfig = MemcacheConfig(policy='Random', memsize='10')
        db.session.add(init_memconfig)
        db.session.commit()

    memsize = init_memconfig.memsize
    policy = init_memconfig.policy
    memcache.set_config(cache_len=int(memsize), policy=policy)

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
    image_path = request.form.get('image_path')
    memcache.requests_num += 1

    if image_key in memcache.keys():
        memcache.pop(image_key)       # invalidate the key in memcache to update key-value

    memcache[image_key] = image_path

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
        image_path = memcache[image_key]
        memcache.cache_hit +=1
        return {'image_path': image_path}
    
    memcache.cache_miss += 1
    return {'image_path': 'not found'}


@memapp.route('/memcache_option',methods=['GET'])
def MemcacheOption():
    mem_config = MemcacheConfig.query.first()

    capacity = request.form['capacity']
    policy = request.form['policy']
    method = request.form['method']
    if method == 'post':
        mem_config.memsize = capacity
        mem_config.policy = policy
        db.session.commit()

        memcache.set_config(cache_len=int(capacity), policy=policy)

    return {'capacity': mem_config.memsize, 'policy': mem_config.policy, 'memcache':memcache}

@memapp.route('/cache_clear',methods=['GET'])
def CacheClear():
    memcache.clear()

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
    total_size = len(memcache)

    request_num = memcache.requests_num

    if memcache.cache_lookup == 0:
        miss_rate = 0
        hit_rate = 0
    else:
        miss_rate = memcache.cache_miss / memcache.cache_lookup
        hit_rate = memcache.cache_hit / memcache.cache_lookup
    
    #store statics in database every 5 seconds
    # tore_statstics_in_database(number_of_items, total_size, request_num, miss_rate, hit_rate)
    #return {'number_of_items':number_of_items, 'total_size':total_size, 'num_of_requests':request_num, 'miss_rate':miss_rate, 'hit_rate':hit_rate,}
    return {'store in database': 'true'}

def store_statstics_in_database(number_of_items, total_size, request_num, miss_rate, hit_rate) -> None:
    mem_statistics = MemcacheStatistics.query.first()
    mem_statistics.num_of_items = number_of_items
    mem_statistics.total_size_of_items = total_size
    mem_statistics.number_of_requests_served  = request_num
    mem_statistics.miss_rate = miss_rate
    mem_statistics.hit_rate = hit_rate
    db.session.commit()

schedule.every(5).seconds.do(Statistics)
while True:
    schedule.run_pending()
    time.sleep(1)