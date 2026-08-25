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

## 8. 踩坑记录（2026-08 实战整理）

### 8.1 国内拉取镜像慢

- Docker Hub 直连极慢，建议用国内镜像源
- 华为云 SWR 同步源（实测可用）：
  `swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/<镜像>:<tag>`
  - `python:3.12-slim`（基础镜像）
  - `jenkins/jenkins:lts-jdk21`（Jenkins 官方，JDK21）
- 拉取后打 tag 用短名：
  `docker tag swr.../python:3.12-slim python:3.12-slim`
- 公共加速器（`daemon.json` 的 `registry-mirrors`）：`dockerproxy.net` 2026-08 实测可用（返回 200）；`docker.m.daocloud.io`、`docker.1ms.run` 可达；`docker.1panel.live` 403 不可用已移除

### 8.2 WSL 2 未安装导致 Docker 无法启动

- 现象：`docker --version` 有输出，但任何命令报
  `cannot find the file specified / pipe dockerDesktopLinuxEngine`
- 解决：管理员终端执行 `wsl --install` → 重启 → `wsl -l -v` 确认
  VERSION=2

### 8.3 Jenkins 版本与插件不兼容

- 现象：安装推荐插件报 `Jenkins (2.504.1) or higher required`、
  `Failed to load: Ionicons API`、`Failed to load: Folders Plugin`
- 原因：华为云源的 `lts-jdk17` tag 是旧 LTS（2.492.1），
  插件更新中心已要求新版本
- 解决：改用 `lts-jdk21` tag（实测 2.516.2）
- 验证版本：`docker run --rm <镜像> sh -c 'unzip -p /usr/share/jenkins/jenkins.war META-INF/MANIFEST.MF | grep Jenkins-Version'`

### 8.4 Jenkins 插件更新源失效

- 现象：日志报
  `FileNotFoundException: mirrors.ustc.edu.cn/jenkins/updates/update-center.json`
- 原因：中科大镜像已下架（华为云/清华/阿里 2026 年均已下架）
- 解决：改回官方源（仅官方源可用，301 重定向正常）
  ```bash
  docker exec -u root jenkins sed -i \
    's|https://mirrors.ustc.edu.cn/jenkins/updates/update-center.json|https://updates.jenkins.io/update-center.json|' \
    /var/jenkins_home/hudson.model.UpdateCenter.xml
  docker restart jenkins
  ```

### 8.5 安装插件后 Jenkins 停止，页面打不开

- 现象：`Exited (5)`，日志 `Scheduling Jenkins reboot`
- 原因：安装插件后 Jenkins 主动重启，但容器未配置自动重启，
  进程退出后容器不会拉起
- 解决：`docker start jenkins`，并加自动重启策略：
  `docker update --restart always jenkins`

### 8.6 publishHTML 缺必填参数

- 现象：`Missing required parameter: "alwaysLinkToLastBuild"`、
  `"allowMissing"`
- 原因：新版 HTML Publisher 插件要求这两个参数
- 解决：Jenkinsfile 中 publishHTML 增加
  `alwaysLinkToLastBuild: true, allowMissing: true`

### 8.7 Jenkins 容器内没有 docker 命令

- 现象：构建报 `/script.sh: 1: docker: not found`（exit 127）
- 原因：挂载 docker.sock 只是提供访问通道，镜像本身不带 docker CLI
- 解决：下载静态二进制（比 apt 快 18 倍，阿里源实测 700KB/s+）：
  ```bash
  docker exec -u root jenkins sh -c '
    cd /tmp && \
    curl -fsSL -o docker.tgz \
      https://mirrors.aliyun.com/docker-ce/linux/static/stable/x86_64/docker-27.3.1.tgz && \
    tar -xzf docker.tgz && \
    mv docker/docker /usr/local/bin/docker && chmod +x /usr/local/bin/docker'
  ```
- 注意：容器重建后需重新安装，建议后续用扩展镜像固化
  （Dockerfile 继承 jenkins 镜像并预装 docker CLI）

### 8.8 Windows Git Bash 路径转换导致挂载失效（隐蔽坑）

- 现象：`docker inspect` 显示挂载变成了
  `/run/desktop/mnt/host/d/Git/var/run/docker.sock`，
  容器内 `/var/run/docker.sock` 不存在
- 原因：Git Bash 会把 `/var/run/docker.sock` 自动转换成
  Windows 路径 `D:\Git\var\run\docker.sock`，挂载到不存在的路径
- 解决：命令前加 `MSYS_NO_PATHCONV=1` 禁用路径转换：
  ```bash
  MSYS_NO_PATHCONV=1 docker run -d --name jenkins \
    -v /var/run/docker.sock:/var/run/docker.sock ...
  ```

### 8.9 凭据 ID 必须显式设置

- 现象：`ERROR: AUTHORIZATION`（environment 引用失败）、
  `Warning: CredentialId "github-credentials" could not be found`
- 原因：凭据添加时未填 ID 字段，Jenkins 自动生成乱码 ID
  （如 `cc49ca37-464a-4043-80f3-fdfff55d3c61`），与 Jenkinsfile 引用不匹配
- 解决：添加凭据时点开 Advanced，**必须手动填 ID**
  （BASE_URL / AUTHORIZATION / CLIENT_ID / REFERENCE_IMAGE_URL）
