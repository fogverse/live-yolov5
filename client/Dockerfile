ARG DREG # docker registry
FROM ${DREG}ariqbasyar/fogverse:input

RUN pip install --upgrade pip
RUN pip install flask flask-socketio

WORKDIR /app
COPY client/client.py .
COPY client/templates/ templates/
COPY fogverse/ fogverse/

CMD ["python", "client.py"]
