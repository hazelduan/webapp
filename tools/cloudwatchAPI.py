import boto3
import datetime

# self.data = {
#             'node_num': 0,
#             'request_num': 0,
#             'hit_num': 0,
#             'miss_num': 0,
#             'lookup_num': 0,
#             'item_num': 0,
#             'total_size': 0.0,
#         }
class cloudwatchAPI():
    def __init__(self):
        self.client = boto3.client('cloudwatch', region_name='us-east-1')
    
    def putMetricData(self, data, metric_label):
        response = self.client.put_metric_data(
            Namespace='memcache',
            MetricData=[
                {
                    'MetricName': metric_label,
                    'Dimensions': [
                        {
                            'Name': 'Statistics',
                            'Value': 'statistics'
                        },
                    ],
                    'Value': data,
                    'Unit': 'Percent'
                },
            ]
        )
        return response
    
    def putMultipleMetric(self, data):
        self.putMetricData(data['node_num'], 'node_num')
        self.putMetricData(data['request_num'], 'request_num')
        self.putMetricData(data['hit_num'], 'hit_num')
        self.putMetricData(data['miss_num'], 'miss_num')
        self.putMetricData(data['lookup_num'], 'lookup_num')
        self.putMetricData(data['item_num'], 'item_num')
        self.putMetricData(data['total_size'], 'total_size')
    
    
    def getMetricData(self, seconds, metric_label, statistics):
        response = self.client.get_metric_statistics(
            Namespace='memcache',
            MetricName=metric_label,
            Dimensions=[{
                'Name': 'Statistics',
                'Value': 'statistics'
            }],

            StartTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds),
            EndTime = datetime.datetime.utcnow(),
            Period = 60,
            Statistics = [statistics],
            Unit = 'Percent'
        )

        return response


    def getAverageMetric(self, seconds, metric_label1, metric_label2):

        res1 = self.getMetricData(seconds, metric_label1, 'Sum')# miss_num or hit_num
        res2 = self.getMetricData(seconds, metric_label2, 'Sum')# lookup_num

        res1_num = res1['Datapoints'][0]
        lookup_num = res2['Datapoints'][0]
        if  lookup_num['Sum'] > 0:
            rate = res1_num['Sum'] / lookup_num['Sum']
        else:
            rate = 0

        return rate
