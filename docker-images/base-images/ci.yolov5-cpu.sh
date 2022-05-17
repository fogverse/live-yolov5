docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ariqbasyar/pytorch:v1.10-py3.8.2-yolov5-cpu \
    -f docker-images/base-images/Dockerfile.yolov5-cpu \
    --push .
