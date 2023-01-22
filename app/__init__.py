from flask import Flask


global memcache

webapp = Flask(__name__)


memcache = {}
webapp.config['SECRET_KEY'] = 'dev' 
from app import main




