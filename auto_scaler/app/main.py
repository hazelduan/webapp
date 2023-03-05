from app import autoscaler, scheduler, cw_api
import requests
import sys
sys.path.append('..')
sys.path.append('..')
from configuration import backend_base_url, base_port


active_node = 8
max_miss_thres = 0.8
min_miss_thres = 0.2
expand_ratio = 2
shrink_ratio = 0.5

def checkMissRate():
    
    # get average miss rate from CloudWatch
    average_miss_rate = cw_api.getAverageMetric(active_node, seconds=60)

    if average_miss_rate > max_miss_thres:      # expand the nodes
        new_active_node = int(active_node * expand_ratio)
        if new_active_node > 8:
            new_active_node = 8

        for mem_port in range(new_active_node, active_node):
            try:
                res = requests.get(backend_base_url + str(mem_port + base_port) + '/start_scheduler')
            except requests.exceptions.ConnectionError:
                print("Can't connect to port " + str(mem_port + base_port))
    elif average_miss_rate < min_miss_thres:    # shrink the nodes
        new_active_node = int(active_node * shrink_ratio)
        if new_active_node < 1:     # no operation, should not shutdown node 1
            return

        for mem_port in range(new_active_node, active_node):
            try:
                res = requests.get(backend_base_url + str(mem_port + base_port) + '/stop_scheduler')
                res = requests.get(backend_base_url + str(mem_port + base_port) + '/cache_clear')
            except requests.exceptions.ConnectionError:
                print("Can't connect to port " + str(mem_port + base_port))

    active_node = new_active_node
    print('current active node : ', active_node)

@autoscaler.route('/update_params', methods=['GET'])
def UpdateParams():
    global active_node
    global max_miss_thres
    global min_miss_thres
    global expand_ratio
    global shrink_ratio

    active_node = requests.form('active_node')
    max_miss_thres = requests.form('max_miss_thres')
    min_miss_thres = requests.form('min_miss_thres')
    expand_ratio = requests.form('expand_ratio')
    shrink_ratio = requests.form('expand_ratio')

# scheduler to store statistics in database
scheduler.add_job(func=checkMissRate, trigger='interval', seconds=10, id='job1')
scheduler.start()