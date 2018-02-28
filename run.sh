#!/bin/bash
deploy_lambda() {
  lambda_reqs
  AWS_ACCOUNT_ID=`aws sts get-caller-identity --output text --query 'Account'`
  S3_BUCKET="lambdacodestore-$AWS_ACCOUNT_ID"
  aws cloudformation package --template template.yml --s3-bucket $S3_BUCKET --output-template lambda-template-export.yml
  aws cloudformation deploy --template lambda-template-export.yml --stack-name DLAppLambdas --capabilities CAPABILITY_IAM
}

node_reqs() {
  npm install
}

build_website() {
  node_reqs
  npm run gulp build
}

environment_reqs() {
  pip install -r env_requirements.txt --upgrade
}

lambda_reqs() {
  pip install -r lambda_requirements.txt -t lambda/requirements/ --upgrade
}

deploy_stack() {
  aws cloudformation deploy --template cfn-template.yml --stack-name DLApp --capabilities CAPABILITY_NAMED_IAM
  aws cloudformation describe-stacks --stack-name DLApp > src/StackOutput.json
  aws cloudformation describe-stacks --stack-name DLApp > lambda/StackOutput.json
}

deploy_website() {
  AWS_ACCOUNT_ID=`aws sts get-caller-identity --output text --query 'Account'`
  S3_BUCKET="website-$AWS_ACCOUNT_ID"
  build_website
  aws s3 cp ./dist/ s3://$S3_BUCKET/ --recursive
}

deploy() {
  deploy_stack
  deploy_lambda
  deploy_website
}

clean() {
  rm -rf node_modules
  rm -rf lambda/requirements/*
  touch lambda/requirements/__init__.py
}

setup() {
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
