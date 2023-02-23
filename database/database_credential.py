try:
    from database import password
except ImportError:
    raise ImportError('Create a password.py file store the password of the database')

db_user = 'admin'
db_password = password.password
db_host = 'database-1.cxz0glvljrqs.us-east-1.rds.amazonaws.com'
db_name = 'webapp_db'

