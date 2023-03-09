import boto3
import datetime

class cloudwatchAPI():
    def __init__(self):
        self.client = boto3.client('cloudwatch', region_name='us-east-1')
    
    def putMetricData(self, node, data, metric_label):
        response = self.client.put_metric_data(
            Namespace='memcache',
            MetricData=[
                {
                    'MetricName': metric_label,
                    'Dimensions': [
                        {
                            'Name': 'node',
                            'Value': str(node)
                        },
                    ],
                    'Value': data,
                    'Unit': 'Percent'
                },
            ]
        )
        return response
    
    def putMultipleMetric(self, node, miss_rate, hit_rate, number_of_items, size_of_items, number_of_requests):
        self.putMetricData(node, miss_rate, 'miss_rate')
        self.putMetricData(node, hit_rate, 'hit_rate')
        self.putMetricData(node, number_of_items, 'number_of_items')
        self.putMetricData(node, size_of_items, 'size_of_items')
        self.putMetricData(node, number_of_requests, 'number_of_requests')
    
    def getMetricData(self, node, seconds, metric_label):
        response = self.client.get_metric_statistics(
            Namespace='memcache',
            MetricName=metric_label,
            Dimensions=[{
                'Name': 'node',
                'Value': str(node)
            }],

            StartTime = datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds),
            EndTime = datetime.datetime.utcnow(),
            Period = 60,
            Statistics = ['Average'],
            Unit = 'Percent'
        )

        return response

    # weight average
    def getAverageMetric(self, active_node, seconds, metric_label):
        miss_rates = []
        for node in range(1, active_node+1):
            res = self.getMetricData(node, seconds, metric_label)
            if len(res['Datapoints']) > 0:
                for miss_rate in res['Datapoints']:
                    miss_rates.append(miss_rate['Average'])
        
        if len(miss_rates) > 0:
            return (sum(miss_rates) / len(miss_rates))
        
        return 0
