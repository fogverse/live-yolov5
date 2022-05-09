ARG DREG # docker registry
FROM ${DREG}ariqbasyar/fogverse:master

WORKDIR /app
COPY master/inference_merger/*.py .
COPY fogverse/ fogverse/
COPY utils/ utils/
CMD ["python", "inference_merger.py"]
