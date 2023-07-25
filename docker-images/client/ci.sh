echo "\$DREG=$DREG"
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DREG}ariqbasyar/fogverse:base-lient \
    --push .
