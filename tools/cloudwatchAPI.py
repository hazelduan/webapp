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
            Statistics = ['Maximum'],
            Unit = 'Percent'
        )

        return response
