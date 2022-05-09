docker buildx build \
    --platform linux/arm64 \
    -t ${DREG}ariqbasyar/fogverse:inference-gpu \
    -f Dockerfile.gpu \
    --push .
