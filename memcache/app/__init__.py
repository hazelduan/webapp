from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
sys.path.append('..')
sys.path.append('..')
from database import database_credential

global memcache

memapp = Flask(__name__)
memcache = {}


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




