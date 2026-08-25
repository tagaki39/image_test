FROM python:3.12-slim

WORKDIR /app

# 先拷贝依赖清单并安装（利用 Docker 层缓存，改代码不用重装依赖）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝项目代码
COPY . .

# pytest-html 不会自动创建报告目录
RUN mkdir -p reports

# 默认命令：跑非生成类用例
CMD ["pytest", "-m", "not costly", "--html=reports/report.html", "--self-contained-html"]
