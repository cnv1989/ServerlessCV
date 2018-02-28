FROM lambci/lambda:build

WORKDIR /app

RUN curl -s https://bootstrap.pypa.io/get-pip.py | python