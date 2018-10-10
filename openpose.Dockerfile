FROM python:3.6-stretch

ARG PYPI_MIRROR=mirrors.aliyun.com

FROM nvidia/cuda:8.0-cudnn5-devel   
# start with the nvidia container for cuda 8 with cudnn 5

LABEL maintainer "Michael Sobrepera <mjsobrep@live.com>"

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install wget unzip lsof apt-utils lsb-core -y
RUN apt-get install libatlas-base-dev -y
RUN apt-get install libopencv-dev python-opencv python-pip -y   

RUN wget https://github.com/CMU-Perceptual-Computing-Lab/openpose/archive/master.zip; \
    unzip master.zip; rm master.zip

WORKDIR openpose-master
RUN sed -i 's/\<sudo chmod +x $1\>//g' ubuntu/install_caffe_and_openpose_if_cuda8.sh; \
    sed -i 's/\<sudo chmod +x $1\>//g' ubuntu/install_openpose_if_cuda8.sh; \
    sed -i 's/\<sudo -H\>//g' 3rdparty/caffe/install_caffe_if_cuda8.sh; \
    sed -i 's/\<sudo\>//g' 3rdparty/caffe/install_caffe_if_cuda8.sh; \
    sync; sleep 1; ./ubuntu/install_caffe_and_openpose_if_cuda8.sh

# pj
RUN apt-get update && apt-get install -y --no-install-recommends \
		build-essential \
		pkg-config \
		libopencv-dev &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY aihub_serve aihub_serve
COPY services/matting matting

# download source code
RUN chmod -R a+w /workspace && \
    cd matting && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt && \
    python3 setup.py install && \
	cd ../aihub_serve && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt && \
	cd ../matting/src && \
    make install

EXPOSE 80

# -H ~/.venv/py3/
ENTRYPOINT uwsgi --http :80 --wsgi-file ./aihub_serve/serve.py --enable-threads --master
