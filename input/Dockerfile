ARG DREG # docker registry
FROM ${DREG}ariqbasyar/final-project:input

WORKDIR /app
COPY input/producer.py .
COPY fogverse/ fogverse/
CMD ["python", "producer.py"]
