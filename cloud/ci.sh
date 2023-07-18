set -x
echo $DREG
docker buildx build \
    --platform linux/amd64 \
    --build-arg DREG=$DREG \
    -t ${DREG}ariqbasyar/fogverse:inference-cpu-cloud-sm \
    -f cloud/Dockerfile \
    --push .
