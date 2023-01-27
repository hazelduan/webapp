from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from collections import OrderedDict
import random
import sys
sys.path.append('..')
sys.path.append('..')
from database import database_credential

global memcache

memapp = Flask(__name__)

## Memcache
class CacheDict(OrderedDict):

    def __init__(self, *args, cache_len: int = 10, policy : str = 'Random', **kwargs):
        self.cache_len = cache_len
        self.policy = policy
        assert policy in ['LRU', 'Random']
        assert cache_len > 0

        super().__init__(*args, **kwargs)
    
    def __setitem__(self, __key, __value) -> None:
        super().__setitem__(__key, __value)
        super().move_to_end(__key)

        while len(self) > self.cache_len:
            if self.policy == 'LRU':
                old_key = next(iter(self))
            elif self.policy == 'Random':
                old_key = random.sample(self.keys(), 1)
                old_key = old_key[0]
            super().__delitem__(old_key)
    
    def __getitem__(self, __key):
        val = super().__getitem__(__key)
        super().move_to_end(__key)
        return val

    
    def set_config(self, cache_len : int, policy : str) -> None:
        self.cache_len = cache_len
        self.policy = policy
        assert policy in ['LRU', 'Random']
        assert cache_len > 0

        while len(self) > self.cache_len:
            if self.policy == 'LRU':
                old_key = next(iter(self))
            elif self.policy == 'Random':
                old_key = random.sample(self.keys(), 1)
                old_key = old_key[0]
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





from app import main




