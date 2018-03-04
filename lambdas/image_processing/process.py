import boto3
import io
import json
import logging
import os
import sys
import zipfile


logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

S3_BUCKET = list(filter(
        lambda output: output.get('OutputKey') == 'ImageStore',
        json.load(open('./StackOutput.json'))["Stacks"][0]["Outputs"]
    ))[0]["OutputValue"]

MODEL_LOCAL_PATH = os.path.join(os.sep, 'tmp', 'yolo_tf.pb')

DL_S3_BUCKET = list(filter(
        lambda output: output.get('OutputKey') == 'DLModelStore',
        json.load(open('./StackOutput.json'))["Stacks"][0]["Outputs"]
    ))[0]["OutputValue"]

REQ_LOCAL_PATH = os.path.join(os.sep, 'tmp', 'requirements')

if not os.path.isdir(REQ_LOCAL_PATH):
    zip_ref = zipfile.ZipFile('requirements.zip', 'r')
    zip_ref.extractall(REQ_LOCAL_PATH)
    zip_ref.close()
    sys.path.insert(0, REQ_LOCAL_PATH)


boto3.setup_default_session(region_name='us-west-2')
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

S3_BUCKET = list(filter(
        lambda output: output.get('OutputKey') == 'ImageStore',
        json.load(open('./StackOutput.json'))["Stacks"][0]["Outputs"]
    ))[0]["OutputValue"]


def handler(event, context):
    from yolo_utils import draw_boxes, eval_image, generate_colors, preprocess_image, load_graph

    # Download Model File
    if not os.path.isdir(MODEL_LOCAL_PATH):
        s3.Bucket(DL_S3_BUCKET).download_file('yolo_tf.pb', MODEL_LOCAL_PATH)
    load_graph(MODEL_LOCAL_PATH)
    os.remove(MODEL_LOCAL_PATH)


    bucket = s3.Bucket(S3_BUCKET)
    image_name = json.loads(event.get('body'))["image_name"]
    image_obj = bucket.Object(image_name)
    file_stream = io.BytesIO()
    out_image_name = "classified-{}".format(image_name)
    image_obj.download_fileobj(file_stream)
    image, image_data = preprocess_image(file_stream, model_image_size=(608, 608))
    file_stream.close()

    scores, boxes, classes = eval_image(image_data, image.size)
    with open('./coco_classes.txt', 'r') as file:
        obj_classes = file.readlines()

    obj_classes = list(map(lambda cls: cls.strip(), obj_classes))
    colors = generate_colors(obj_classes)
    draw_boxes(image, scores, boxes, classes, obj_classes, colors)
    file_stream = io.BytesIO()
    image.save(file_stream, format=image.format, quality=90)
    file_stream.seek(0)
    s3_client.put_object(Body=file_stream, Bucket=S3_BUCKET, Key=out_image_name, ACL='public-read')
    file_stream.close()
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Headers":
                "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods":
                "DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT",
            "Access-Control-Allow-Origin":
                "*"
        },
        'body': json.dumps({
            'image_name': image_name,
            'classified_image_name': out_image_name
        })
    }
