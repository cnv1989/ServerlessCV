import sys
sys.path.insert(0,'./requirements')

import boto3
import json

s3 = boto3.resource('s3')

STACK_OUTPUT = json.load(open('./StackOutput.json'))

def resize_image(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
