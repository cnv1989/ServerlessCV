FROM amazonlinux:latest

RUN yum install -y python36
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.6/install.sh | bash

WORKDIR /app
COPY . .

RUN pip install -r env_requirements.txt
RUN pip install -r lambda_requirements.txt -t lambda/requirements/
