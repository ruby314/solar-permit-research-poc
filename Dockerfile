FROM ubuntu:22.04

# avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# update and install Python 3.11 (preferred langchain python version)
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# set python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# required by python md2pdf package
RUN apt update && \
    apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0
#RUN apt install libcairo2 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# upgrade pip
RUN python3.11 -m pip install --upgrade pip

# set working directory
WORKDIR /app

# install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install md2pdf==1.0.1

# copy python code
COPY . .

# run the script
ENTRYPOINT ["python", "main.py"]