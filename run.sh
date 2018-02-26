#!/bin/bash

venv() {
  pip install virtualenv
  virtualenv -p python3 env
}

deploy_lambda() {
  lambda_reqs
  AWS_ACCOUNT_ID=`env/bin/aws sts get-caller-identity --output text --query 'Account'`
  S3_BUCKET="lambdacodestore-$AWS_ACCOUNT_ID"
  env/bin/aws cloudformation package --template template.yml --s3-bucket $S3_BUCKET --output-template lambda-template-export.yml
  env/bin/aws cloudformation deploy --template lambda-template-export.yml --stack-name DLAppLambdas --capabilities CAPABILITY_IAM
}


build_website() {
  npm install
  npm run gulp build
}

environment_reqs() {
  env/bin/pip install -r env_requirements.txt --upgrade
}

lambda_reqs() {
  env/bin/pip install -r lambda_requirements.txt -t lambda/requirements/ --upgrade
}

deploy_stack() {
  env/bin/aws cloudformation deploy --template cfn-template.yml --stack-name DLApp --capabilities CAPABILITY_NAMED_IAM
  env/bin/aws cloudformation describe-stacks --stack-name DLApp > src/StackOutput.json
  env/bin/aws cloudformation describe-stacks --stack-name DLApp > lambda/StackOutput.json
}

deploy_website() {
  AWS_ACCOUNT_ID=`env/bin/aws sts get-caller-identity --output text --query 'Account'`
  S3_BUCKET="website-$AWS_ACCOUNT_ID"
  build_website
  env/bin/aws s3 cp ./dist/ s3://$S3_BUCKET/ --recursive
}

deploy() {
  deploy_stack
  deploy_lambda
  deploy_website
}

setup() {
  venv
  environment_reqs
  lambda_reqs
}

case $1 in
  deploy)
    deploy
    ;;
  deploy_stack)
    deploy_stack
    ;;
  deploy_lambda)
    deploy_lambda
    ;;
  deploy_website)
    deploy_website
    ;;
  lambda_reqs)
    lambda_reqs
    ;;
  setup)
    setup
    ;;
  venv)
    venv
    ;;
  *)
    echo "Usage: $0 {venv|setup|deploy_website|deploy_lambda|deploy_stack}"
esac
