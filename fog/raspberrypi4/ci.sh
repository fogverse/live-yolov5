set -x
echo $DREG
docker buildx build \
    --platform linux/arm64 \
    --build-arg DREG=$DREG \
    -t ${DREG}ariqbasyar/fogverse:preprocess-raspberrypi-sm \
    -f fog/raspberrypi4/Dockerfile \
    --push .
