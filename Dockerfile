#FROM ubuntu:latest
FROM python:2.7

COPY ./requirements.txt /app/requirements.txt
COPY ./setup.* /app/
COPY ./yadagetemplates/*.py /app/yadagetemplates/

WORKDIR /app

RUN pip install --no-cache-dir -e .

EXPOSE 5000
CMD ["python", "yadagetemplates"]
