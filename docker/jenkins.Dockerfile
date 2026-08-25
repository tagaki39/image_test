# 固化 Jenkins 容器环境：预装 docker CLI（容器重建不丢失）
# 构建：docker build -f docker/jenkins.Dockerfile -t jenkins-ci:1.0 .
# 使用：见 docker-compose.yml

FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/jenkins/jenkins:lts-jdk21

USER root

# 预装 docker CLI（阿里源静态二进制，无依赖，快）
RUN curl -fsSL -o /tmp/docker.tgz \
      https://mirrors.aliyun.com/docker-ce/linux/static/stable/x86_64/docker-27.3.1.tgz \
    && tar -xzf /tmp/docker.tgz -C /tmp \
    && mv /tmp/docker/docker /usr/local/bin/docker \
    && chmod +x /usr/local/bin/docker \
    && rm -rf /tmp/docker /tmp/docker.tgz \
    && docker --version

USER jenkins
