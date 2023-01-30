#!../venv/bin/python
from app import webapp

from app import db
db.drop_all()
db.create_all()

webapp.run('0.0.0.0',5001,debug=False)


