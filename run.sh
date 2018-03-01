#!/bin/bash

venv() {
  pip install virtualenv
  virtualenv -p python3 env
}

build_lambda() {
  docker-compose up && docker-compose down
}

deploy_lambda() {
  AWS_ACCOUNT_ID=`env/bin/aws sts get-caller-identity --output text --query 'Account'`
  S3_BUCKET="lambdacodestore-$AWS_ACCOUNT_ID"
  env/bin/aws cloudformation package --template template.yml --s3-bucket $S3_BUCKET --output-template lambda-template-export.yml
  env/bin/aws cloudformation deploy --template lambda-template-export.yml --stack-name DLAppLambdas --capabilities CAPABILITY_IAM
}

node_reqs() {
  rm -rf node_modules
  npm install
}

build_website() {
  node_reqs
  npm run gulp build
}

environment_reqs() {
  env/bin/pip install -r env_requirements.txt --upgrade
}

lambda_reqs() {
  pushd dl_lambdas
  rm -rf requirements/*
  touch requirements/__init__.py
  pip install -r requirements.txt -t requirements/ --upgrade
  pushd requirements
  rm -r external
  rm -r pip
  rm -r pip-9.0.1.dist-info
  rm -r wheel
  rm -r wheel-0.30.0.dist-info
  rm easy_install.py
  find . -name \*.pyc -delete
  pushd google
  touch __init__.py
  popd
  popd
  popd
}

deploy_stack() {
  env/bin/aws cloudformation deploy --template cfn-template.yml --stack-name DLApp --capabilities CAPABILITY_NAMED_IAM
  env/bin/aws cloudformation describe-stacks --stack-name DLApp > src/StackOutput.json
  env/bin/aws cloudformation describe-stacks --stack-name DLApp > dl_lambdas/StackOutput.json
}

deploy_models() {
  AWS_ACCOUNT_ID=`env/bin/aws sts get-caller-identity --output text --query 'Account'`
  S3_BUCKET="dlmodelstore-$AWS_ACCOUNT_ID"
  env/bin/aws s3 cp ./models/ s3://$S3_BUCKET/ --recursive
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
  deploy_models)
    deploy_models
    ;;
  lambda_reqs)
    lambda_reqs
    ;;
  build_lambda)
    build_lambda
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
