ARG DREG # docker registry
FROM ${DREG}ariqbasyar/fogverse:inference-gpu

RUN pip3 install flask flask-socketio simple-websocket

WORKDIR /app
COPY fog/jetson_nano/scenario1/inference.py .
COPY fog/jetson_nano/scenario1/templates/ templates/
COPY fogverse/ fogverse/
CMD ["python3", "inference.py"]
