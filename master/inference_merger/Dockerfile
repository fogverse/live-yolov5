ARG DREG # docker registry
FROM ${DREG}ariqbasyar/fogverse:inference-cpu

WORKDIR /app
RUN git clone --depth=1 --branch=v6.1 https://github.com/ultralytics/yolov5.git \
    && cp -r yolov5/utils/ utils/
COPY master/inference_merger/*.py .
COPY fogverse/ fogverse/
CMD ["python", "inference_merger.py"]
