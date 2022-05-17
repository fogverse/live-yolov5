docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DREG}ariqbasyar/fogverse:preprocess \
    -f docker-images/master/Dockerfile \
    --push .
