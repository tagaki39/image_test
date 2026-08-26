FROM python:3.12-slim

WORKDIR /app

# 先拷贝依赖清单并安装（利用 Docker 层缓存，改代码不用重装依赖）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 allure-commandline（阿里 Maven 镜像，生成 Allure 报告用）
RUN curl -fsSL -o /tmp/allure.zip \
      https://maven.aliyun.com/repository/central/io/qameta/allure/allure-commandline/2.29.0/allure-commandline-2.29.0.zip \
    && python -m zipfile -e /tmp/allure.zip /opt \
    && rm -f /tmp/allure.zip \
    && ln -s /opt/allure-2.29.0/bin/allure /usr/local/bin/allure \
    && allure --version

# 拷贝项目代码
COPY . .

# pytest-html 不会自动创建报告目录
RUN mkdir -p reports

# 默认命令：跑非生成类用例（--html 已在 pytest.ini addopts 配置）
CMD ["pytest", "-m", "not costly"]
