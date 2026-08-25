# 阿里云部署计划（Jenkins 迁移）

> 目标：把 Jenkins 从本机迁移到阿里云，获得公网可达性，
> 实现 GitHub Webhook 秒级自动触发。

## 一、为什么迁移

| 维度 | 本机 Jenkins | 阿里云 Jenkins |
|------|:---:|:---:|
| 公网可达 | ❌ 不行 | ✅ 有公网 IP |
| 24 小时在线 | ❌ 关电脑就没了 | ✅ 一直在线 |
| 自动触发 | 轮询 SCM（最长 5 分钟延迟） | ✅ Webhook 秒级 |
| 成本 | 电费 | ~50-100 元/月 |

核心收益：**git push → GitHub → Jenkins 自动构建**（秒级触发）。

## 二、采购建议（阿里云轻量应用服务器）

| 配置 | 推荐值 |
|------|--------|
| 规格 | 2 核 2G |
| 系统 | Ubuntu 22.04 |
| 带宽 | 3-5M |
| 费用 | 新用户首年约几十元/月 |

> 2 核 2G 跑 Jenkins + Docker 足够（Java 约占用 1G）。

## 三、迁移步骤（约 1 小时）

### 1. 服务器准备

- 购买轻量服务器，记下公网 IP + root 密码
- 控制台安全组放行 8080 端口

### 2. 安装 Docker

```bash
ssh root@你的公网IP
curl -fsSL https://get.docker.com | sh
systemctl enable docker
```

### 3. 部署 Jenkins（复用现成配置）

```bash
git clone https://github.com/tagaki39/image_test.git
cd image_test
docker build -f docker/jenkins.Dockerfile -t jenkins-ci:1.0 .
docker compose up -d
```

### 4. 初始化

- 浏览器打开 `http://你的公网IP:8080`
- 初始密码：`docker logs jenkins`
- 安装推荐插件 → 创建管理员 → 设置强密码

### 5. 重配凭据（5 个，与本机相同）

| 凭据 ID | 类型 |
|---------|------|
| BASE_URL | Secret text |
| AUTHORIZATION | Secret text（当前有效 Token） |
| CLIENT_ID | Secret text |
| REFERENCE_IMAGE_URL | Secret text |
| github-credentials | Username with password |

### 6. 新建流水线任务

同本机配置：Pipeline script from SCM → GitHub 仓库 → Jenkinsfile

### 7. 配置 GitHub Webhook

```
GitHub 仓库 → Settings → Webhooks → Add webhook
Payload URL:  http://你的公网IP:8080/github-webhook/
Content type: application/json
Events:      Just the push event
```

### 8. 任务触发器

任务配置 → 触发器 → 勾选 `GitHub hook trigger for GITScm polling`

### 9. 验证

```bash
git commit --allow-empty -m "test webhook" && git push
# 观察 Jenkins 是否在 1-2 秒内自动开始构建
```

## 四、安全清单（公网暴露必做）

- [ ] 初始密码拿完即改，设置强密码
- [ ] 安全组只放行自己的 IP（IP 白名单）
- [ ] 确认 CSRF 保护开启（默认开启）
- [ ] 邮件通知配置完成（及时发现异常）

## 五、迁移影响

| 项 | 影响 |
|------|------|
| 代码/流水线/镜像 | 平台无关，直接复用，零修改 |
| 构建历史 | 本机卷中的数据不迁移（新环境重新积累） |
| 本机 Jenkins | 可保留可删除，无冲突 |
| 邮件配置 | 需在服务器 Jenkins 重新配置 SMTP |
