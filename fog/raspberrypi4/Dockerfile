ARG DREG # docker registry
FROM ${DREG}ariqbasyar/fogverse:preprocess

WORKDIR /app
COPY fog/raspberrypi4/preprocess.py .
COPY fogverse/ fogverse/
CMD ["python", "preprocess.py"]
