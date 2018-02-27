import sys
sys.path.insert(0,'./requirements')

import boto3
import json
import logging

from PIL import Image


logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

s3 = boto3.resource('s3')

S3_BUCKET = list(filter(
        lambda output: output.get('OutputKey') == 'ImageStore',
        json.load(open('./StackOutput.json'))["Stacks"][0]["Outputs"]
    ))[0]["OutputValue"]

def classify_image(event, context):
    key = json.loads(event.get('body'))["image_name"]
    obj = s3.Object(S3_BUCKET, key)
    try:
        body = obj.get()['Body'].read()
        pil_image = Image.open(body)
        return {
            'statusCode': 200,
            'body': "pil_image"
        }
    except Exception as e:
        logger.error(str(e))
        raise e
