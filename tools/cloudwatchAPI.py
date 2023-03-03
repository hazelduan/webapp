import boto3
import datetime

class cloudwatchAPI():
    def __init__(self):
        self.client = boto3.client('cloudwatch', region_name='us-east-1')
    
    def putMeticData(self, node, data):
        response = self.client.put_metric_data(
            Namespace='memcache',
            MetricData=[
                {
                    'MetricName': 'miss_rate',
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
    
    def getMetricData(self, node, seconds):
        response = self.client.get_metric_statistics(
            Namespace='memcache',
            MetricName='miss_rate',
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


    def getAverageMetric(self, active_node, seconds):
        miss_rates = []
        for node in range(1, active_node+1):
            res = self.getMetricData(node, seconds)
            if len(res['Datapoints']) > 0:
                for miss_rate in res['Datapoints']:
                    miss_rates.append(miss_rate['Average'])
        
        if len(miss_rates) > 0:
            return (sum(miss_rates) / len(miss_rates))
        
        return 0
