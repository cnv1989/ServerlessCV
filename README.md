# Serverless Computer Vision

This repo is an attempt at setting up serverless deep learning applications using AWS services. For this implementation I have used TensorFlow but the stack can be used with any application/framework.

You can leverage this package and its packages to build your own pipeline using AWS.

## Frontend

* [React](https://reactjs.org/)
* [Redux](https://redux.js.org/)

## Backend

* [S3](https://aws.amazon.com/s3/)
* [AWS Lambda](https://aws.amazon.com/lambda/)
* [API Gateway](https://aws.amazon.com/api-gateway/)

## Deployment & Testing

* [AWS Cloudformation](https://aws.amazon.com/cloudformation/)
* [Docker](https://www.docker.com/)
* [aws-sam-local](https://github.com/awslabs/aws-sam-local)


## Stack Files

* [cfn-template.yml](/cfn-template.yml) - Cloudformation template to setup necessary S3 buckets, Cognito Authentication, IAM roles and policies
* [template.yml](/template.yml) - Contains SAM template for Lambda function and API Gateway
* [swagger.yml](/swagger.yml) - Contains API specifications
* [run.sh](/run.sh) - Bash script containing all the necessary commands to setup and deploy the stack.

![Stack](/readme-images/cfnstack.png)

## Setup Instructions

1. Copy/Download the model(s) into [/models](/models) directory.
```bash
    wget https://www.dropbox.com/s/h8ywy9lp8siw0ml/yolo_tf.pb -P models/
```
2. Deploy the entire stack
```bash
    bash run.sh deploy
```

### OR

2. Deploy the basic stack containing S3, Cognito and IAM.
```bash
    bash run.sh deploy_stack
```

3. Upload model(s) to S3 bucket.
```bash
    bash run.sh deploy_model
```

4. Build and deploy static assest i.e entire frontend built using React
```bash
    bash run.sh deploy_website
```

5. Build and deploy lambdas
```bash
    bash run.sh deploy_lambdas
```

