FROM python:3.6-stretch

ARG PYPI_MIRROR=mirrors.aliyun.com

WORKDIR /workspace

COPY aihub_serve aihub_serve
COPY models/mask_rcnn models/mask_rcnn
COPY services/mask_rcnn mask_rcnn

# download source code
RUN chmod -R a+w /workspace && \
    cd mask_rcnn/src && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt && \
    cd .. && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt && \
    python3 setup.py install && \
	cd ../aihub_serve && \
    pip3 install -i http://${PYPI_MIRROR}/pypi/simple/ --trusted-host ${PYPI_MIRROR} -r requirements.txt

ENV AIHUB_MODELS=/workspace/models
EXPOSE 80

# -H ~/.venv/py3/
ENTRYPOINT uwsgi --http :80 --wsgi-file ./aihub_serve/serve.py --enable-threads --master
