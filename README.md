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

1. Setup `virtualenv` and install `node_modules`
```bash
    bash run.sh setup
```

2. Create IAM user on AWS with admin access and use the accesskey and secret
```
    bash run.sh aws_config
```

3. Deploy the entire stack
```bash
    bash run.sh deploy
```

4. Copy/Download the model(s) into [/models](/models) directory.
```bash
    wget https://www.dropbox.com/s/h8ywy9lp8siw0ml/yolo_tf.pb -P models/
```

### OR

4. Deploy the basic stack containing S3, Cognito and IAM.
```bash
    bash run.sh deploy_stack
```

5. Upload model(s) to S3 bucket.
```bash
    bash run.sh deploy_model
```

6. Build and deploy static assest i.e entire frontend built using React
```bash
    bash run.sh deploy_website
```

7. Build and deploy lambdas
```bash
    bash run.sh deploy_lambdas
```


## Development & Testing

* Follow the first 3 steps from setup instructions.

* Run the local node server locally.
```
    npm run watch
```

* Open `http://localhost:3000/` in the browser

* Drop images in the application to upload them to S3.

* Once the images are in S3 you can use `sam local` to test lambda functions.
```
    npm run sam local invoke ProcessImage -- --event fixtures/ProcessImage.json
```
