docker buildx build \
    --platform linux/arm64 \
    -t ariqbasyar/pytorch:v1.9-py3.6.9-yolov5-gpu \
    -f docker-images/base-images/Dockerfile.yolov5-gpu \
    --push .
