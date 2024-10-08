from flask import render_template, url_for, request
from app import memapp, memcache
from flask import json
from app import db, MemcacheConfig, MemcacheStatistics, CUR_NODE, cw_api
import sys
import os
import logging
import base64

sys.path.append("..")
sys.path.append("..")
from configuration import base_path, backend_base_url
import hashlib

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


@memapp.route('/put', methods=['POST'])
def put():
    image_key = request.form.get('image_key')
    image_content = request.form.get('image_content')
    memcache.requests_num += 1
    logging.info("------------------------------------")
    logging.info("PPPPUUUUUUUUUUUUTTTTT BBB")
    logging.info("------------------------------------")
    if image_key in memcache.keys():
        memcache.pop(image_key)  # invalidate the key in memcache to update key-value

    memcache[image_key] = image_content
    logging.info("------------------------------------")
    logging.info("IIIIIIIIIIIIIIIIIIIIIIIN PPPPPP")
    logging.info("------------------------------------")
    response = {
        "success": "true",
        "key": image_key
    }
    return response


@memapp.route('/get', methods=['GET'])
def get():
    image_key = request.form.get('image_key')
    memcache.requests_num += 1
    memcache.cache_lookup += 1
    logging.info("BBBBBBBEFORE")
    if image_key in memcache:
        logging.info("AAAAAAAAAAAAAFTER")
        image_content = memcache[image_key]
        # decoded_image = image_content.decode()
        memcache.cache_hit +=1
        return {'image_content': image_content, 'cache_hit': 'true'}
    
    memcache.cache_miss += 1
    return {'image_content': 'not found', 'cache_hit': 'false'}


@memapp.route('/get_partition_images', methods=['GET'])
def get_partition_images():
    partition = request.form.get('partition')
    images = list()
    image_keys = list()
    if memcache.keys():
        for key in list(memcache.keys()):
            # print("content" + memcache[key])
            image_content = memcache[key]
            image_key_md5 = hashlib.md5(key.encode('utf-8')).hexdigest()
            # print("image_key_md5: ", image_key_md5)
            # print("image_key", image_key)
            if int(image_key_md5[0], 16) == int(partition):
                image_keys.append(key)
                images.append(image_content)
        for image_key in list(image_keys):
            memcache.pop(image_key)  # delete images in this partition from memcache
    data = {'image_keys': image_keys, 'images': images}
    response = memapp.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


@memapp.route('/put_partition_images', methods=['GET'])
def put_partition_images():
    i = 0
    images = request.json['images']  # encoded image content
    image_keys = request.json['image_keys']
    print('images received', image_keys)
    if image_keys:
        for key in image_keys: 
            image_content = images[i]
            memcache[key] = image_content
            i += 1
    print('images put into memcache', memcache.keys())
    return {'success': 'true'}
    


@memapp.route('/memcache_option', methods=['GET', 'POST'])
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


@memapp.route('/cache_clear', methods=['GET'])
def CacheClear():
    memcache.clear()
    memcache.cur_size = 0
    return {'success': 'true'}


@memapp.route('/key_invalidate', methods=['GET'])
def InvalidateKey():
    image_key = request.form['image_key']
    if image_key in memcache.keys():
        memcache.pop(image_key)


@memapp.route('/display_keys', methods=['GET'])
def DisplayKeys():
    # res = cw_api.getAverageMetric(CUR_NODE, 60, 'miss_rate')

    # print("Average: ", res)
    
    return render_template('display_keys.html', memcache=memcache)

@memapp.route('/get_item_statistics', methods=['GET'])
def GetItemStatistics():
    number_of_items = len(memcache.keys())
    total_size = memcache.cur_size
    return {'number_of_items': number_of_items, 'total_size': total_size}

# @memapp.route('/statistics', methods=['GET'])
# def Statistics():
#     number_of_items = len(memcache.keys())
#     # total_size = len(memcache)
#     total_size = memcache.cur_size

#     request_num = memcache.requests_num

#     if memcache.cache_lookup == 0:
#         miss_rate = 0
#         hit_rate = 0
#     else:
#         miss_rate = memcache.cache_miss / memcache.cache_lookup
#         hit_rate = memcache.cache_hit / memcache.cache_lookup
    
#     # provide current time to mysql time format
#     cur_time = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-5]

#     #store statics in database every 5 seconds
#     store_statistics_in_cloudwatch(cur_time, number_of_items, total_size, request_num, miss_rate, hit_rate)
#     return {'store in database': 'true'}


# def store_statistics_in_cloudwatch(cur_time, number_of_items, total_size, request_num, miss_rate, hit_rate):
#     cw_api.putMultipleMetric(CUR_NODE, miss_rate, hit_rate, number_of_items, total_size, request_num)


# def store_statistics_in_database() -> None:
#     with memapp.app_context():
#         cur_time = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-5]
#         mem_statistics = MemcacheStatistics()
#         mem_statistics.mem_node = CUR_NODE
#         mem_statistics.time = cur_time
#         mem_statistics.num_of_items = cw_api.getAverageMetric(CUR_NODE, 60, 'number_of_items')
#         mem_statistics.total_size_of_items = cw_api.getAverageMetric(CUR_NODE, 60, 'size_of_items')
#         mem_statistics.number_of_requests_served  = cw_api.getAverageMetric(CUR_NODE, 60, 'number_of_requests')
#         mem_statistics.miss_rate = cw_api.getAverageMetric(CUR_NODE, 60, 'miss_rate')
#         mem_statistics.hit_rate = cw_api.getAverageMetric(CUR_NODE, 60, 'hit_rate')
#         db.session.add(mem_statistics)
#         db.session.commit()



# @memapp.route('/stop_scheduler', methods=['GET'])
# def StopScheduler():
#     scheduler.pause_job('job1')
#     scheduler.pause_job('job2')
#     return 'stop scheduler'


# @memapp.route('/start_scheduler', methods=['GET'])
# def StartScheduler():
#     scheduler.resume_job('job1')
#     scheduler.resume_job('job2')
#     return 'start scheduler'

# # scheduler to store statistics in database
# scheduler.add_job(func=Statistics, trigger='interval', seconds=5, id='job1')
# scheduler.add_job(func=store_statistics_in_database, trigger='interval', seconds=60, id='job2')
# scheduler.start()


