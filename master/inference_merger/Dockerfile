ARG DREG # docker registry
FROM ${DREG}ariqbasyar/final-project:master-inference-merger

WORKDIR /app
COPY master/inference_merger/*.py .
COPY fogverse/ fogverse/
COPY utils/ utils/
CMD ["python", "inference_merger.py.py"]
