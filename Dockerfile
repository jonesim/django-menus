ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION}

ARG REQUIREMENTS=requirements.txt
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY ${REQUIREMENTS} /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt
#copy dist/*.* /app/
