import sys
sys.path.insert(0,'./requirements')

import boto3
import imghdr
import io
import json
import logging
import numpy as np
import os


import imghdr
import tensorflow as tf

from PIL import Image
from yolo_utils import *


MODELS = {
    'YOLO': {
        'functionName': 'Yolo',
        'image_size': (608, 608)
    }
}

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

s3.Bucket(DL_S3_BUCKET).download_file('yolo_tf.pb', MODEL_LOCAL_PATH)


def handler(event, context):
    bucket = s3.Bucket(S3_BUCKET)
    image_name = json.loads(event.get('body'))["image_name"]
    image_obj = bucket.Object(image_name)
    file_stream = io.BytesIO()
    out_image_name = "classified-{}".format(image_name)
    image_output_path = os.path.join(os.sep, 'tmp', out_image_name)
    image_obj.download_fileobj(file_stream)
    pil_image = Image.open(file_stream)
    out_image = eval_image(pil_image)
    out_image.save(image_output_path, quality=90)
    s3_client.upload_file(image_output_path, S3_BUCKET, out_image_name)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'image_name': image_name,
            'classified_image_name': out_image_name
        })
    }


def preprocess_image(image, model_image_size):
    resized_image = image.resize(tuple(reversed(model_image_size)), Image.BICUBIC)
    image_data = np.array(resized_image, dtype='float32')
    image_data /= 255.
    image_data = np.expand_dims(image_data, 0)  # Add batch dimension.
    return image, image_data


def get_grid_indices(output_layer, grid):
    width_indices = tf.range(0, grid[1])
    width_indices = tf.tile(tf.expand_dims(width_indices, axis=0), (grid[0], 1))
    height_indices = tf.range(0, grid[0])
    height_indices = tf.tile(tf.expand_dims(height_indices, axis=0), (grid[1], 1))
    height_indices = tf.transpose(height_indices)
    indices = tf.stack([width_indices, height_indices], axis=-1)
    indices = tf.reshape(indices, (1, grid[0], grid[1], 1, 2))
    return tf.cast(indices, output_layer[0].dtype)


def unroll_boxes(output_layer, anchors, num_classes):
    num_anchors = len(anchors)
    anchors_tensor = tf.reshape(tf.Variable(anchors), [1, 1, 1, num_anchors, 2])

    grid = tf.shape(output_layer)[1:3]

    grid_indices = get_grid_indices(output_layer, grid)

    output_layer = tf.reshape(output_layer, [-1, grid[0], grid[1], num_anchors, num_classes + 5])
    grid = tf.cast(tf.reshape(grid, [1, 1, 1, 1, 2]), output_layer.dtype)

    box_centers = tf.sigmoid(output_layer[..., :2])
    box_dims = tf.exp(output_layer[..., 2:4])
    box_confidence = tf.sigmoid(output_layer[..., 4:5])
    box_class_probs = tf.nn.softmax(output_layer[..., 5:])

    box_centers = tf.divide(tf.add(box_centers, grid_indices), grid)
    box_dims = tf.divide(tf.multiply(box_dims, anchors_tensor), grid)

    return box_centers, box_dims, box_confidence, box_class_probs


def boxes_to_corners(box_centers, box_dims):
    box_mins = box_centers - (box_dims / 2.)
    box_maxes = box_centers + (box_dims / 2.)

    return tf.concat([
        box_mins[..., 1:2],
        box_mins[..., 0:1],
        box_maxes[..., 1:2],
        box_maxes[..., 0:1]
    ], axis=-1)


def filter_boxes(box_confidence, boxes, box_class_probs, threshold=0.6):
    box_scores = tf.multiply(box_confidence, box_class_probs)
    box_classes = tf.argmax(box_scores, axis=-1)
    box_class_scores = tf.reduce_max(box_scores, axis=-1)
    filtering_mask = box_class_scores >= threshold
    scores = tf.boolean_mask(box_class_scores, filtering_mask)
    boxes = tf.boolean_mask(boxes, filtering_mask)
    classes = tf.boolean_mask(box_classes, filtering_mask)
    return scores, boxes, classes


def non_max_suppression(scores, boxes, classes, max_boxes=10, iou_threshold=0.5):
    max_boxes_tensor = tf.Variable(max_boxes, dtype='int32')     # tensor to be used in tf.image.non_max_suppression()
    nms_indices = tf.image.non_max_suppression(boxes, scores, max_boxes_tensor, iou_threshold)
    scores = tf.gather(scores, nms_indices)
    boxes = tf.gather(boxes, nms_indices)
    classes = tf.gather(classes, nms_indices)
    return scores, boxes, classes


def get_boxes(output_layer, anchors, classes, image_shape=(720., 1280.)):
    num_classes = len(classes)
    box_centers, box_dims, box_confidence, box_class_probs = unroll_boxes(output_layer, anchors, num_classes)
    boxes = boxes_to_corners(box_centers, box_dims)
    scores, boxes, classes = filter_boxes(box_confidence, boxes, box_class_probs)
    boxes = scale_boxes(boxes, image_shape)
    scores, boxes, classes = non_max_suppression(scores, boxes, classes)
    return scores, boxes, classes


def load_graph(model_file):
    graph = tf.Graph()
    graph_def = tf.GraphDef()

    with open(model_file, "rb") as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def)

    return graph


def eval_image(pil_image):
    obj_classes = open('./coco_classes.txt', 'r').readlines()
    obj_classes = list(map(lambda cls: cls.strip(), obj_classes))
    anchors = [[0.57273, 0.677385], [1.87446, 2.06253], [3.33843, 5.47434], [7.88282, 3.52778], [9.77052, 9.16828]]
    colors = generate_colors(obj_classes)
    image, image_data = preprocess_image(pil_image, model_image_size=(608, 608))
    image_size = image.size

    graph = load_graph(MODEL_LOCAL_PATH)

    with graph.as_default():
        input_name = "import/" + "input_1"
        output_name = "import/" + "output_0"
        input_operation = graph.get_operation_by_name(input_name)
        output_operation = graph.get_operation_by_name(output_name)
        scores, boxes, classes = get_boxes(output_operation.outputs, anchors, obj_classes,
                                           image_shape=(float(image_size[1]), float(image_size[0])))
        init_op = tf.global_variables_initializer()
        with tf.Session() as sess:
            sess.run(init_op)
            [out_scores, out_boxes, out_classes] = sess.run([scores, boxes, classes],
                                                            feed_dict={input_operation.outputs[0]: image_data})
            draw_boxes(image, out_scores, out_boxes, out_classes, obj_classes, colors)
            return image
