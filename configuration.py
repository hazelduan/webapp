import os

cur_folder_path = os.path.dirname(__file__)    # current file path
base_path = cur_folder_path
file_system_path = os.path.join(base_path, 'file_storage')
backend_base_url = 'http://127.0.0.1:5001'