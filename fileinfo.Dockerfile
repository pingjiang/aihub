FROM python:3.6-stretch

ARG PYPI_MIRROR=mirrors.aliyun.com

RUN apt-get update && apt-get install -y --no-install-recommends \
		build-essential \
		pkg-config \
		libopencv-dev &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY aihub_serve aihub_serve
COPY services/fileinfo fileinfo

# download source code
RUN chmod -R a+w /workspace && \
    cd fileinfo && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt && \
    python3 setup.py install && \
	cd ../aihub_serve && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt

EXPOSE 80

# -H ~/.venv/py3/
ENTRYPOINT uwsgi --http :80 --wsgi-file ./aihub_serve/serve.py --enable-threads --master
