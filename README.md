# Serverless Computer Vision

This repo is an attempt at setting up serverless computer vision applications using AWS services. For this implementation I have used TensorFlow but the stack can be used with any application/framework.

You can leverage this package and its packages to build your own pipeline using AWS.

## Frontend

* [React](https://reactjs.org/)
* [Redux](https://redux.js.org/)

## Backend

* [S3](https://aws.amazon.com/s3/)
* [AWS Lambda](https://aws.amazon.com/lambda/)
* [API Gateway](https://aws.amazon.com/api-gateway/)
* [Cognito](https://aws.amazon.com/cognito/ )

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

## Requirements

* [nodejs](https://nodejs.org/en/)
* [Python](https://www.python.org/downloads/)
* [pip](https://pip.pypa.io/en/stable/installing/)
* [viratulenv](https://virtualenv.pypa.io/en/stable/)

## Setup Instructions

1. Setup `virtualenv` and install `node_modules`
```bash
    bash run.sh setup
```

2. Create IAM user on AWS with admin access and use the access_key and secret_key to configure aws credentials locally.
```
    bash run.sh aws_config
```

3. Copy/Download the model(s) into [/models](/models) directory. You can use my Yolo model for this setup
```bash
    wget https://www.dropbox.com/s/h8ywy9lp8siw0ml/yolo_tf.pb -P models/
```

4. Deploy the entire stack
```bash
    bash run.sh deploy
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

* Follow the first 4 steps from setup instructions.

* Start the api locally
```
    npm run sam local start-api
```

* Replace API_URL in [/src/actions/index.jsx](https://github.com/cnv1989/ServerlessDeeplearningWebapp/blob/master/src/actions/index.jsx#L17) with the local url.

* Run the local node server locally.
```
    npm run watch
```

* Open [http://localhost:3000/](http://localhost:3000/) in the browser

* Drop images in the application to upload them to S3.


* If you want to debug the function you can invoke the function locally once the images are in S3. The will generate better logs.

```
    npm run sam local invoke ProcessImage -- --event fixtures/ProcessImage.json
```

## Webpage

![Webpage](/readme-images/website.png)


## Lambda Limits

* Code Size: 261 Mb
* Persistant Storage: 512 Mb
