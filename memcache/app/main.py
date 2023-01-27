
from flask import render_template, url_for, request
from app import memapp, memcache
from flask import json

from app import db, MemcacheConfig

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

    if image_key in memcache.keys():
        memcache.pop(image_key)                         # invalidate the key in memcache
    
    memcache[image_key] = image_path

    response = {
        "success" : "true",
        "key" : image_key
    }
    return response

@memapp.route('/get',methods=['GET'])
def get():
    image_key = request.form.get('image_key')

    if image_key in memcache:
        image_path = memcache[image_key]
        return {'image_path': image_path}
    
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


