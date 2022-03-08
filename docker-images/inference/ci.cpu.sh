docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DREG}ariqbasyar/final-project:inference-cpu \
    -f Dockerfile.cpu \
    --push .

