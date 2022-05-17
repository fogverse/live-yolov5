docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ariqbasyar/opencv:v4.5.5-py3.8.10 \
    -f docker-images/base-images/Dockerfile.opencv \
    --push .
