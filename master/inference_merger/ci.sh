set -x
echo "$DREG"
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DREG}ariqbasyar/fogverse:master-inference-merger \
    -f master/inference_merger/Dockerfile \
    --push .
