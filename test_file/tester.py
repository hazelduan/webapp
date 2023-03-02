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

ratio = 4
time_cost = []
total_start_time = time.time()




## read/write 1:4
# for num_read in range(1,201,20):
#     num_write = num_read * 4

#     write_list = list(range(num_write))
#     random.shuffle(write_list)   # randomly write

#     read_list = []
#     for _ in range(num_read):
#         read_list.append(random.randint(0, num_write))

#     start_time = time.time()
    
#     for key in write_list:
#         response = requests.post(url+'/api/upload', files=file_1, data={'key':f'test_{key}'})

    
#     for key in read_list:
#         response = requests.post(url+'/image_lookup', data={'image_key':f'test_{key}'})

#     end_time = time.time()
#     response = requests.post(url+'/api/delete_all')
#     print(f"num_read : {num_read}, num_write: {num_write}, time_cost : {end_time - start_time}")
#     time_cost.append(end_time - start_time)

## read/write 1:1
for num_read in range(1,501,50):
    num_write = num_read * 1

    write_list = list(range(num_write))
    random.shuffle(write_list)   # randomly write

    read_list = []
    for _ in range(num_read):
        read_list.append(random.randint(0, num_write))

    start_time = time.time()
    
    for key in write_list:
        response = requests.post(url+'/api/upload', files=file_1, data={'key':f'test_{key}'})

    
    for key in read_list:
        response = requests.post(url+'/image_lookup', data={'image_key':f'test_{key}'})

    end_time = time.time()
    response = requests.post(url+'/api/delete_all')
    print(f"num_read : {num_read}, num_write: {num_write}, time_cost : {end_time - start_time}")
    time_cost.append(end_time - start_time)


# ## read/write 4:1
# for num_write in range(1,201,20):
#     num_read = num_write * 4

#     write_list = list(range(num_write))
#     random.shuffle(write_list)   # randomly write

#     read_list = []
#     for _ in range(num_read):
#         read_list.append(random.randint(0, num_write))

#     start_time = time.time()
    
#     for key in write_list:
#         response = requests.post(url+'/api/upload', files=file_1, data={'key':f'test_{key}'})

    
#     for key in read_list:
#         response = requests.post(url+'/image_lookup', data={'image_key':f'test_{key}'})

#     end_time = time.time()
#     response = requests.post(url+'/api/delete_all')
#     print(f"num_read : {num_read}, num_write: {num_write}, time_cost : {end_time - start_time}")
#     time_cost.append(end_time - start_time)

total_end_time = time.time()
print("total time cost :", total_end_time - total_start_time)

save_file = open('time_result.txt', 'w')
for val in time_cost:
    save_file.write(str(round(val, 2)) + ", ")
save_file.close()

