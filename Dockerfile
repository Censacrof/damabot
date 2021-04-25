FROM python:3.8
WORKDIR /usr/src/app
RUN pip install --no-cache-dir discord==1.0.1 emoji==0.6.0 jsonschema==3.2.0
COPY . .
ENTRYPOINT [ "python", "./damabot.py"]