from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from collections import OrderedDict
import random
from flask_apscheduler import APScheduler
import sys
sys.path.append('..')
sys.path.append('..')
from database import database_credential

global memcache

memapp = Flask(__name__)

# Scheduler

class Config(object):
    SCHEDULER_API_ENABLED = True


memapp.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(memapp)




## Memcache
class CacheDict(OrderedDict):

    def __init__(self, *args, cache_size: int = 3096, policy : str = 'Random', **kwargs):
        super().__init__(*args, **kwargs)

        assert policy in ['LRU', 'Random']
        assert cache_size > 0

        self.cache_size = cache_size
        self.policy = policy
        
        self.cur_size = 0
        self.requests_num = 0
        
        self.cache_lookup = 0
        self.cache_miss = 0
        self.cache_hit = 0

        
    
    def __setitem__(self, __key, __value) -> None:
        super().__setitem__(__key, __value)
        super().move_to_end(__key)
        self.cur_size += int(len(__value) / 1024) # in KB
        while self.cur_size > self.cache_size:
            if self.policy == 'LRU':
                old_key = next(iter(self))
            elif self.policy == 'Random':
                old_key = random.sample(self.keys(), 1)
                old_key = old_key[0]
            old_value = super().__getitem__(old_key)
            self.cur_size -= int(len(old_value) / 1024)
            super().__delitem__(old_key)
            
    
    def __getitem__(self, __key):
        val = super().__getitem__(__key)
        super().move_to_end(__key)
        return val

    
    def set_config(self, cache_size : int, policy : str) -> None:
        assert policy in ['LRU', 'Random']
        assert cache_size > 0

        self.cache_size = cache_size
        self.policy = policy
        

        while self.cur_size > self.cache_size:
            if self.policy == 'LRU':
                old_key = next(iter(self))
            elif self.policy == 'Random':
                old_key = random.sample(self.keys(), 1)
                old_key = old_key[0]
            old_value = super().__getitem__(old_key)
            self.cur_size -= int(len(old_value) / 1024)
            super().__delitem__(old_key)

    def pop(self, __key):
        super().__delitem__(__key)


memcache = CacheDict()


db_user = database_credential.db_user
db_password = database_credential.db_password
db_host = database_credential.db_host
db_name = database_credential.db_name
memapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(db_user, db_password, db_host, db_name)

db = SQLAlchemy(memapp)

class MemcacheConfig(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    policy = db.Column(db.String(50))
    memsize = db.Column(db.String(10))

class MemcacheStatistics(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    time = db.Column(db.Time)
    num_of_items = db.Column(db.Integer)
    total_size_of_items = db.Column(db.Integer)
    number_of_requests_served = db.Column(db.Integer)
    miss_rate = db.Column(db.Float)
    hit_rate = db.Column(db.Float)


with memapp.app_context():
    # Initialize memcache config
    init_memconfig = MemcacheConfig.query.first()

    if init_memconfig == None:              # when the database is created initially
        init_memconfig = MemcacheConfig(policy='Random', memsize='3096')
        db.session.add(init_memconfig)
        db.session.commit()

    memsize = init_memconfig.memsize
    policy = init_memconfig.policy
    memcache.set_config(cache_size=int(memsize), policy=policy)

    # Initialize memcache statistics
    init_memstatistics = MemcacheStatistics.query.first()

    if init_memstatistics == None:
        init_memstatistics = MemcacheStatistics(
            num_of_items = 0,
            total_size_of_items = 0,
            number_of_requests_served = 0,
            miss_rate = 0,
            hit_rate = 0
        )
        db.session.add(init_memstatistics)
        db.session.commit()
from app import main




