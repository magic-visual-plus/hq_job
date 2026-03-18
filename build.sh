# 构建镜像
docker build -t hq-job-server .

# 运行容器
docker run -d -p 8000:8000 \
  -e AUTODL_TOKEN=your_autodl_token \
  -e API_TOKEN=your_api_token \
  hq-job-server