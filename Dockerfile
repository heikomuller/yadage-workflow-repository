FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY ./requirements.txt /app/requirements.txt
COPY ./yadagewfrepo/*.py /app/
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "./server.py"]
