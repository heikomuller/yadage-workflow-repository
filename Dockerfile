FROM fedora
RUN dnf install -y gcc gcc-c++ graphviz-devel ImageMagick python-devel libffi-devel openssl openssl-devel unzip nano autoconf automake libtool redhat-rpm-config; dnf clean all

COPY ./requirements.txt /app/requirements.txt
COPY ./setup.* /app/
COPY ./yadagetemplates/*.py /app/yadagetemplates/
WORKDIR /app

RUN curl https://bootstrap.pypa.io/get-pip.py | python -
RUN curl https://get.docker.com/builds/Linux/x86_64/docker-1.9.1  -o /usr/bin/docker && chmod +x /usr/bin/docker
RUN pip install -e .

EXPOSE 5000
CMD ["python", "yadagetemplates"]
