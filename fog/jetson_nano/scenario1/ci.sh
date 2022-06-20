set -x
echo $DREG
docker buildx build \
    --platform linux/arm64 \
    --build-arg DREG=$DREG \
    -t ${DREG}ariqbasyar/fogverse:inference-gpu-jetson-sc1 \
    -f fog/jetson_nano/scenario1/Dockerfile \
    --push .
