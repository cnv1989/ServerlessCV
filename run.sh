#!/bin/bash


venv() {
  pip install virtualenv
  virtualenv -p python3 env
}

build_lambda() {
  docker-compose up && docker-compose down
}

deploy_lambdas() {
  AWS_ACCOUNT_ID=`env/bin/aws sts get-caller-identity --output text --query 'Account'`
  S3_BUCKET="lambdacodestore-$AWS_ACCOUNT_ID"
  AWS_REGION='us-west-2'
  sed "s/region_placeholder/$AWS_REGION/g" 'swagger.yml' | sed "s/account_placeholder/$AWS_ACCOUNT_ID/g" > swagger-export.yml
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

LAMBDA_DIRS="image_processing"

lambda_reqs() {
  pushd lambdas
  for dir in $LAMBDA_DIRS
  do
    pushd $dir
    mkdir requirements
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
    if [ -d "google" ]; then
      touch google/__init__.py
    fi
    zip -r ../requirements.zip .
    popd
    rm -rf requirements
    popd
  done
  popd
}

deploy_stack() {
  env/bin/aws cloudformation deploy --template cfn-template.yml --stack-name DLApp --capabilities CAPABILITY_NAMED_IAM
  env/bin/aws cloudformation describe-stacks --stack-name DLApp > src/StackOutput.json
  for dir in $LAMBDA_DIRS
  do
    env/bin/aws cloudformation describe-stacks --stack-name DLApp > lambdas/$dir/StackOutput.json
  done
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
  deploy_models
  deploy_lambdas
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
  deploy_lambdas)
    deploy_lambdas
    ;;
  deploy_website)
    deploy_website
    ;;
  deploy_models)
    deploy_models
    ;;
  build_lambda)
    build_lambda
    ;;
  build_website)
    build_website
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
    echo "Usage: $0 {venv|setup|deploy_website|deploy_lambdas|deploy_stack|build_website|build_lambdas|build_stack}"
esac
