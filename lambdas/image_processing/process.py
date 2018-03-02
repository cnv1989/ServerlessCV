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


# Download Model File

MODEL_LOCAL_PATH = os.path.join(os.sep, 'tmp', 'yolo_tf.pb')

DL_S3_BUCKET = list(filter(
        lambda output: output.get('OutputKey') == 'DLModelStore',
        json.load(open('./StackOutput.json'))["Stacks"][0]["Outputs"]
    ))[0]["OutputValue"]

s3.Bucket(DL_S3_BUCKET).download_file('yolo_tf.pb', MODEL_LOCAL_PATH)

REQ_LOCAL_PATH = os.path.join(os.sep, 'tmp', 'requirements')
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
    from yolo_utils import draw_boxes, eval_image, generate_colors, preprocess_image

    bucket = s3.Bucket(S3_BUCKET)
    image_name = json.loads(event.get('body'))["image_name"]
    image_obj = bucket.Object(image_name)
    file_stream = io.BytesIO()
    out_image_name = "classified-{}".format(image_name)
    image_output_path = os.path.join(os.sep, 'tmp', out_image_name)
    image_obj.download_fileobj(file_stream)
    image, image_data = preprocess_image(file_stream, model_image_size=(608, 608))

    scores, boxes, classes = eval_image(image_data, image.size)

    obj_classes = open('./coco_classes.txt', 'r').readlines()
    obj_classes = list(map(lambda cls: cls.strip(), obj_classes))
    colors = generate_colors(obj_classes)
    draw_boxes(image, scores, boxes, classes, obj_classes, colors)

    image.save(image_output_path, quality=90)
    s3_client.upload_file(image_output_path, S3_BUCKET, out_image_name)
    s3_client.put_object_acl(Bucket=S3_BUCKET, Key=out_image_name, ACL='public-read')

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
