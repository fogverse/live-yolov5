set -x
echo "$DREG"
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DREG}ariqbasyar/fogverse:master-forwarder \
    -f master/message_forwarder/Dockerfile \
    --push .
