from app import autoscaler, scheduler, cw_api
from flask import request
import requests
import sys
import logging

sys.path.append('..')
sys.path.append('..')
from configuration import backend_base_url, manager_port, MODE

logger = logging.getLogger()
logger.setLevel(logging.INFO)



is_on = False
active_node = 8
max_miss_thres = 0.8
min_miss_thres = 0.2
expand_ratio = 2
shrink_ratio = 0.5
local_public_ip = ''

if MODE == 'LOCAL':
    local_public_ip = backend_base_url

@autoscaler.route('/autocheck_miss', methods=['POST'])
def checkMissRate():
    if not is_on:
        return {'success' : 'true'}
    global active_node
    global max_miss_thres
    global min_miss_thres
    global expand_ratio
    global shrink_ratio

    # get average miss rate from CloudWatch

    #average_miss_rate = cw_api.getAverageMetric(seconds=60, metric_label1='miss_num', metric_label2='lookup_num')
    logging.info("before active node" + str(active_node))
    logging.info(request.form['miss_rate'])
    average_miss_rate = float(request.form['miss_rate'])
    
    logging.info("average_miss_rate" + str(average_miss_rate))
    logging.info("max_miss_thres:" + str(max_miss_thres))
    if average_miss_rate > max_miss_thres:      # expand the nodes

        active_node = int(active_node * expand_ratio)
        if active_node > 8:
            active_node = 8

    elif average_miss_rate < min_miss_thres:  # shrink the nodes
        active_node = int(active_node * shrink_ratio)
        if active_node < 1:  # no operation, should not shutdown node 1
            active_node = 1

    logging.info('after active node : '+  str(active_node))
    response = requests.post(local_public_ip + str(manager_port) + '/resize', data={'new_node_number': active_node})

    return {'success' : 'true'}


@autoscaler.route('/update_local_ip', methods=['POST'])
def UpdateLocalIP():
    global local_public_ip
    if MODE == 'CLOUD':
        local_public_ip = request.form['local_public_ip']


@autoscaler.route('/update_active_node', methods=['POST'])
def UpdateActiveNode():
    global active_node
    active_node = int(request.form['active_node'])

    return {'success' : 'true'}

@autoscaler.route('/update_params', methods=['POST'])
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

    print(active_node, max_miss_thres, min_miss_thres, expand_ratio, shrink_ratio)

    return {'success': 'true'}


@autoscaler.route('/turn_on_auto_scaler', methods=['POST'])
def turn_on_auto_scaler():
    global is_on
    is_on = True
    return {'success' : 'true'}


@autoscaler.route('/turn_off_auto_scaler', methods=['POST'])
def turn_off_auto_scaler():
    global is_on
    is_on = False
    return {'success' : 'true'}

# scheduler to store statistics in database
# scheduler.add_job(func=checkMissRate, trigger='interval', seconds=60, id='job1')
# scheduler.start()
