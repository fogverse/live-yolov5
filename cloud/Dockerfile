ARG DREG # docker registry
FROM ${DREG}ariqbasyar/final-project:inference-cpu

WORKDIR /app
COPY fogverse .
COPY cloud/inference-2.py .
CMD ["python", "inference.py"]
