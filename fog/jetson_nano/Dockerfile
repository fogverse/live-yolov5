ARG DREG # docker registry
FROM ${DREG}ariqbasyar/final-project:inference-gpu

WORKDIR /app
COPY fog/jetson_nano/inference.py .
COPY fogverse/ fogverse/
CMD ["python", "inference.py"]
