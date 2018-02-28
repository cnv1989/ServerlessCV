FROM amazonlinux:latest

WORKDIR /app

RUN yum install -y python36
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.8/install.sh | bash