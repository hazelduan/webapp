import os

cur_folder_path = os.path.dirname(__file__)    # current file path
base_path = cur_folder_path
file_system_path = os.path.join(base_path, 'file_storage')
backend_base_url = 'http://127.0.0.1:'
frontend_port = 5000
base_port = 5001  #memcache base port 
auto_scaler_port = 5020
manager_port = 5001
EC2_AMI = 'ami-080ff70d8f5b80ba5'
EC2_NODE_ID = ['i-011344a69579f4aba',
               'i-028f59ff595181eea',
               'i-04811c8f5d5fb6455',
               'i-068ee2b540ea556f7',
               'i-0757db71e1d5bec4a',
               'i-017560a4e490ebc36',
               'i-01df643f09d09cbfe',
               'i-0e4a431271f974132']
EC2_CONTROL_ID = ['i-064c51778e3ba3a0e']

               