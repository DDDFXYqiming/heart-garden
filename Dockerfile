FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据库
RUN python -c "from app.main import init_db; init_db()"

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app/main.py"]
