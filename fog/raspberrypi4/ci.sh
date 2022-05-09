set -x
echo $DREG
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg DREG=$DREG \
    -t ${DREG}ariqbasyar/fogverse:preprocess-raspberrypi \
    -f fog/raspberrypi4/Dockerfile \
    --push .
