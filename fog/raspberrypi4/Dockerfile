ARG DREG # docker registry
FROM ${DREG}ariqbasyar/final-project:preprocess

WORKDIR /app
COPY fogverse .
COPY fog/raspberrypi4/preprocess-2.py .
CMD ["python", "preprocess-2.py"]
