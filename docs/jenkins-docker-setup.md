# Docker + Jenkins 接入指南

## 1. 启动 Jenkins（关键：挂载 docker.sock）

Jenkins 的 Pipeline 里要执行 `docker build` / `docker run`，
必须让 Jenkins 容器能使用宿主机的 Docker，所以要挂载 docker.sock：

```bash
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

> Windows 使用 Docker Desktop 时 `/var/run/docker.sock` 路径会自动转换，直接照抄即可。

**注意：** 之前没用 `-v /var/run/docker.sock` 启动过的，需要先删除重建：

```bash
docker rm -f jenkins
# 然后用上面的完整命令重新启动
```

## 2. 初始化

```bash
docker logs jenkins        # 查看初始密码
```

浏览器打开 `http://localhost:8080` → 输密码 → 安装推荐插件 → 创建管理员。

## 3. 插件（系统管理 → 插件管理）

```
Git / Pipeline / HTML Publisher / Email Extension
```

## 4. 凭据（系统管理 → Credentials）

| 凭据 ID | 类型 | 内容 |
|---------|------|------|
| BASE_URL | Secret text | https://test.xywhaigc.top |
| AUTHORIZATION | Secret text | Bearer eyJ0eXAi... |
| CLIENT_ID | Secret text | e5cd7e48... |
| REFERENCE_IMAGE_URL | Secret text | https://minio...png |
| github-credentials | Username with password | GitHub 账号/Token |

## 5. 新建流水线任务

```
新建任务 → image-api-test → 流水线
定义 → Pipeline script from SCM
SCM → Git → 仓库地址 → github-credentials → Script Path = Jenkinsfile
```

## 6. 构建

点"立即构建"。Stage View 依次走：

```
Checkout → Build Test Image → Fast Tests → (手动触发才跑 Full Tests)
```

## 7. 常见问题

| 现象 | 原因 | 解决 |
|------|------|------|
| pipeline 里 docker 命令报错 | Jenkins 容器没挂载 docker.sock | 删容器用第 1 步完整命令重建 |
| 报告找不到 | publishHTML 的 reportDir 与卷挂载路径不一致 | 检查 `-v "$PWD/reports:/app/reports"` |
| 构建很慢 | 首次拉 python 镜像 + 装依赖 | 第二次开始走 Docker 缓存 |
