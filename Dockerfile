# 使用Python官方镜像作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY requirements.txt .
COPY app.py .
COPY tts_service.py .
COPY utils1.py .
COPY logger_config.py .

# 安装依赖包
RUN pip install --no-cache-dir -r requirements.txt

# 创建语音列表目录
RUN mkdir -p "语音列表"

# 声明环境变量（生产环境中可以通过Docker run参数或.env文件覆盖）
# API密钥环境变量
ENV API_KEY=4b7c9e2a-3d8f-5a1b-6c4d-7e8f9a0b1c2d
# IP白名单环境变量（格式：逗号分隔的IP列表）
# 注意：在Docker容器中，localhost指向容器本身，不是宿主机的localhost
# 如果需要允许从宿主机访问，不需要在此处设置localhost
# 推荐在运行容器时通过--env参数动态设置允许的IP
ENV ALLOWED_IPS=

# 声明容器运行时监听的端口
EXPOSE 5001

# 声明容器运行时的默认命令
CMD ["python", "app.py"]