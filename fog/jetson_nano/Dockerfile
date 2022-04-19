ARG DREG # docker registry
FROM ${DREG}ariqbasyar/final-project:inference-gpu

WORKDIR /app
COPY fogverse .
COPY fog/jetson-nano/full-2.py .
CMD ["python", "full-2.py"]
