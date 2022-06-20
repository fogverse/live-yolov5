ARG DREG # docker registry
FROM ${DREG}ariqbasyar/fogverse:master

WORKDIR /app
COPY master/message_forwarder/forwarder.py .
COPY fogverse/ fogverse/
CMD ["python", "forwarder.py"]
