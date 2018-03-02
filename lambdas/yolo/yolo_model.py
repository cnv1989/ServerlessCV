import boto3
import json
import os
import sys
import zipfile


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


import numpy as np
import tensorflow as tf


def classify(event, context):
    json_file = event["json_file"]

    content_object = s3.Object(S3_BUCKET, json_file)
    file_content = content_object.get()['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)
    image_data = np.array(json_content['image_data'])
    image_size = json_content['image_size']
    scores, boxes, classes = eval_image(image_data, image_size)
    return {
        'scores': scores.tolist(),
        'boxes': boxes.tolist(),
        'classes': classes.tolist()
    }


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


def scale_boxes(boxes, image_shape):
    """ Scales the predicted boxes in order to be drawable on the image"""
    height = image_shape[0]
    width = image_shape[1]
    image_dims = tf.stack([height, width, height, width])
    image_dims = tf.reshape(image_dims, [1, 4])
    boxes = boxes * image_dims
    return boxes


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


def eval_image(image_data, image_size):
    obj_classes = open('./coco_classes.txt', 'r').readlines()
    obj_classes = list(map(lambda cls: cls.strip(), obj_classes))
    anchors = [[0.57273, 0.677385], [1.87446, 2.06253], [3.33843, 5.47434], [7.88282, 3.52778], [9.77052, 9.16828]]

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
            return sess.run([scores, boxes, classes], feed_dict={input_operation.outputs[0]: image_data})
