set -x
echo $DREG
docker buildx build \
    --platform linux/amd64 \
    --build-arg DREG=$DREG \
    -t ${DREG}ariqbasyar/fogverse:client \
    -f client/Dockerfile \
    --load .
