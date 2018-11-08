#!/bin/sh

# docker build -t aihub_mask_rcnn -f mask_rcnn.Dockerfile .
# # docker build -t aihub_face_alignment -f face_alignment.Dockerfile .
# # docker build -t aihub_matting -f matting.Dockerfile .


# docker tag aihub_mask_rcnn pingjiang/aihub_mask_rcnn:latest
# docker push pingjiang/aihub_mask_rcnn:latest

docker build -t aihub_fileinfo -f fileinfo.Dockerfile .
docker tag aihub_fileinfo pingjiang/aihub_fileinfo:latest
docker push pingjiang/aihub_fileinfo:latest