docker buildx build \
    --platform linux/arm64 \
    -t ${DREG}ariqbasyar/final-project:inference-gpu \
    -f Dockerfile.gpu \
    --push .

