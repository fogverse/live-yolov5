docker buildx build \
    --platform linux/arm64 \
    -t ariqbasyar/pytorch:v1.9-py3.6.9-yolo-jetpack \
    -f docker-images/base-images/Dockerfile.yolo-jetpack \
    --push .
