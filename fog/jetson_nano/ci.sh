set -x
echo $DREG
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg DREG=$DREG \
    -t ${DREG}ariqbasyar/final-project:inference-gpu-jetson \
    -f cloud/Dockerfile \
    --push .
