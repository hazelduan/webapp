from app import autoscaler, scheduler, cw_api
from flask import request
import requests
import sys
sys.path.append('..')
sys.path.append('..')
from configuration import backend_base_url, base_port, manager_port


active_node = 8
max_miss_thres = 0.8
min_miss_thres = 0.2
expand_ratio = 2
shrink_ratio = 0.5

def checkMissRate():
    global active_node
    global max_miss_thres
    global min_miss_thres
    global expand_ratio
    global shrink_ratio
    # get average miss rate from CloudWatch
    average_miss_rate = cw_api.getAverageMetric(active_node=active_node, seconds=60)

    if average_miss_rate > max_miss_thres:      # expand the nodes
        new_active_node = int(active_node * expand_ratio)
        if new_active_node > 8:
            new_active_node = 8

    elif average_miss_rate < min_miss_thres:    # shrink the nodes
        new_active_node = int(active_node * shrink_ratio)
        if new_active_node < 1:     # no operation, should not shutdown node 1
            return


    active_node = new_active_node
    print('current active node : ', active_node)
    response = requests.post(backend_base_url + str(manager_port) + '/resize_manual', data={'new_node_number': active_node})

@autoscaler.route('/update_params', methods=['GET'])
def UpdateParams():
    global active_node
    global max_miss_thres
    global min_miss_thres
    global expand_ratio
    global shrink_ratio

    active_node = int(request.form['active_node'])

    max_miss_thres = float(request.form['Max_Miss_Rate_threshold'])
    min_miss_thres = float(request.form['Min_Miss_Rate_threshold'])
    expand_ratio = float(request.form['expandRatio'])
    shrink_ratio = float(request.form['shrinkRatio'])

    return {'success' : 'true'}

# scheduler to store statistics in database
scheduler.add_job(func=checkMissRate, trigger='interval', seconds=60, id='job1')
scheduler.start()