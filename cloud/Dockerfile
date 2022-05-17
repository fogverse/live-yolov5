ARG DREG # docker registry
FROM ${DREG}ariqbasyar/fogverse:inference-cpu

WORKDIR /app
COPY fogverse/ fogverse/
COPY cloud/inference.py .
CMD ["python", "inference.py"]
