import requests
import os
import time
import random
url = "http://127.0.0.1:5000"


# upload image
filename = ['Joseph.jpg', 'snow.jpg']
workdir = os.path.abspath(os.getcwd())
file_1 = {'file': open(os.path.join(workdir,'test_file', filename[0]), 'rb')}
file_2 = {'file': open(os.path.join(workdir,'test_file', filename[1]), 'rb')}


num_read = 800

num_write = 200

write_list = list(range(num_write))
random.shuffle(write_list)

read_list = []
for _ in range(num_read):
    read_list.append(random.randint(0, num_write))

start_time = time.time()
cnt = 0
cnt_list = []
for key in write_list:
    response = requests.post(url+'/api/upload', files=file_1, data={'key':f'test_{key}'})
    cnt += 1
    cur_time = time.time()
    if cur_time - start_time >= 0.1:
        cnt_list.append(cnt)
        cnt = 0
        start_time = cur_time

start_time = time.time()
for key in read_list:
    response = requests.post(url+'/image_lookup', data={'image_key':f'test_{key}'})
    cnt += 1
    cur_time = time.time()
    if cur_time - start_time >= 0.1:
        cnt_list.append(cnt)
        cnt = 0
        start_time = cur_time

response = requests.post(url+'/api/delete_all')
save_file = open('throu_result.txt', 'w')
for val in cnt_list:
    save_file.write(str(val) + ", ")
save_file.close()

