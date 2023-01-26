from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
global memcache

webapp = Flask(__name__)


memcache = {}
webapp.config['SECRET_KEY'] = 'dev' 


from app import main




