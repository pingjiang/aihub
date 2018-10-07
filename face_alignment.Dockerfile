FROM python:3.6-stretch

ARG PYPI_MIRROR=mirrors.aliyun.com

RUN apt-get update && apt-get install -y --no-install-recommends \
		build-essential \
		cmake \
		git \
		curl \
		vim \
		ca-certificates \
		libboost-all-dev \
		libjpeg-dev \
		libpng-dev &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY aihub_serve aihub_serve
COPY models models
COPY services/face_alignment face_alignment

# download source code
RUN chmod -R a+w /workspace && \
    cd face_alignment && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt && \
    python3 setup.py install && \
	cd ../aihub_serve && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt

ENV AIHUB_MODELS=/workspace/models
EXPOSE 80

# -H ~/.venv/py3/
ENTRYPOINT uwsgi --http :80 --wsgi-file ./aihub_serve/serve.py --enable-threads --master
