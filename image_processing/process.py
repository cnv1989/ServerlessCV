import sys
sys.path.insert(0,'./requirements')

import boto3
import imghdr
import io
import json
import logging
import numpy as np

from PIL import Image


MODELS = {
    'YOLO': {
        'functionName': 'Yolo',
        'image_size': (608, 608)
    }
}

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

s3 = boto3.resource('s3')

session = boto3.Session()
logger.info(session.get_credentials())

S3_BUCKET = list(filter(
        lambda output: output.get('OutputKey') == 'ImageStore',
        json.load(open('./StackOutput.json'))["Stacks"][0]["Outputs"]
    ))[0]["OutputValue"]


def preprocess_image(image, model_image_size):
    resized_image = image.resize(tuple(reversed(model_image_size)), Image.BICUBIC)
    image_data = np.array(resized_image, dtype='float32')
    image_data /= 255.
    image_data = np.expand_dims(image_data, 0)  # Add batch dimension.
    return image, image_data


def handler(event, context):
    bucket = s3.Bucket(S3_BUCKET)
    image_obj = bucket.Object(json.loads(event.get('body'))["image_name"])
    file_stream = io.BytesIO()
    model = MODELS['YOLO']
    image_obj.download_fileobj(file_stream)
    try:
        pil_image = Image.open(file_stream)
        image, image_data = preprocess_image(pil_image, model['image_size'])
        return {
            'statusCode': 200,
            'body': np.array_str(image_data)
        }
    except Exception as e:
        logger.error(str(e))
        raise e
