# 项目成果总结

> 用于简历、面试、绩效汇报的直接素材。

## 一、项目一句话

基于 **pytest + requests** 的图片生成接口自动化测试框架，接入 **Docker 容器化 + Jenkins 持续集成**，实现代码提交后自动构建、自动测试、自动报告的全流程闭环。

## 二、技术栈

| 分类 | 技术 |
|------|------|
| 测试框架 | Python / pytest / requests / pytest-html / pytest-xdist |
| 容器化 | Docker / Docker Compose / Dockerfile |
| CI/CD | Jenkins Declarative Pipeline / HTML Publisher / Email Extension |
| 版本管理 | Git / GitHub |
| 环境 | Windows + WSL2 / Linux |

## 三、实现的功能

### 测试框架层
- 覆盖**鉴权、异常参数、任务提交、异步轮询、结果校验、任务列表、参数变体** 7 类场景，共 17 条用例
- 分层架构：`api`（HTTP 封装）→ `services`（业务逻辑/轮询）→ `tests`（用例断言），fixture 链式注入
- 异步任务状态机轮询（进行中/成功/失败/未知状态显式处理），超时保护 240s
- 参数化测试：异常用例数据与代码分离（JSON 驱动）；参数变体（尺寸/比例/数量 3 维度 × 3 取值）pytest 参数化，提交后校验字段回显
- 测试标记体系（smoke / negative / auth / costly / slow），按需选择性执行

### CI/CD 层
- **Declarative Pipeline**：Checkout → Build Image → Fast Tests → Full Tests → 报告归档 → 邮件通知
- 阶段化策略：非生成类用例每次提交自动跑（秒级）；真实 AI 生成用例仅手动触发（省钱）
- **Docker 容器化**：测试镜像保证环境一致；Jenkins 镜像固化（预装 docker CLI），compose 一键部署
- 敏感信息管理：Token/凭据全部走 Jenkins Credentials，不入代码库、不落镜像

## 四、关键成果数据

| 指标 | 数据 |
|------|------|
| 用例数 | 17 条（7 类场景） |
| Fast Tests 耗时 | ~0.6s（非生成类） |
| Full Tests 耗时 | ~90s+（含 1 次完整 AI 生成 + 9 次参数变体提交） |
| 参数变体 | 尺寸 3（512/1024/2048）、比例 3（1:1/16:9/9:16）、数量 3（1/2/4） |
| 流水线阶段 | 5 个（含报告归档） |
| 报告 | 2 份 HTML 报告，构建侧边栏直接查看 |
| 发现的问题 | 后端 2 个参数校验缺口（空 prompt、count=0 提交阶段未拦截） |

## 五、技术亮点（面试可展开）

1. **异步任务轮询状态机**：显式枚举进行中/成功/失败，未知状态快速失败，避免"挂到超时才发现"
2. **DinD（Docker-in-Docker）实践**：Jenkins 容器挂载宿主 docker.sock + 静态二进制 CLI，避开复杂嵌套
3. **报告导出方案选型**：`-v` 挂载源路径被宿主 daemon 解析导致文件丢失 → 改用 `docker cp` + `set +e` 保证失败时报告仍导出
4. **凭据安全**：敏感值仅存在于 Jenkins Credentials 与 .env（gitignore），镜像构建排除 `.env`
5. **环境可复现**：固化镜像 + docker-compose，新机器 2 条命令起整套 CI

## 六、踩坑记录（解决问题的真实过程）

| # | 问题 | 方案 |
|---|------|------|
| 1 | 国内拉取 Docker Hub 镜像慢 | 华为云 SWR 同步源 + 加速器（dockerproxy.net 实测可用） |
| 2 | WSL2 未装导致 Docker 不可用 | `wsl --install` + 重启 |
| 3 | Jenkins 版本与插件不兼容（插件要求 ≥2.504，镜像 2.492） | 换 lts-jdk21 镜像（2.516.2） |
| 4 | 中科大 Jenkins 更新源 404（镜像站 2026 全部下架） | 改回官方 updates.jenkins.io |
| 5 | 装插件后 Jenkins 停止页面打不开 | `--restart always` 自动拉起 |
| 6 | publishHTML 缺必填参数 | 补 alwaysLinkToLastBuild / allowMissing |
| 7 | 容器内无 docker 命令 | 阿里源静态二进制（比 apt 快 18 倍） |
| 8 | Git Bash 路径转换导致 socket 挂载失效 | MSYS_NO_PATHCONV=1 |
| 9 | 凭据 ID 自动乱码导致流水线引用失败 | 添加凭据时手动指定 ID |
| 10 | sh -e 导致测试失败时报告未导出 | set +e 包住 docker run，退出码显式传递 |
| 11 | 残留容器名冲突 | run 前 docker rm -f 幂等清理 |

完整版见 [jenkins-docker-setup.md](jenkins-docker-setup.md)。

## 七、简历项目描述（可直接使用）

> **图片生成接口自动化测试框架**（Python + pytest + Docker + Jenkins）
>
> - 基于 pytest + requests 搭建接口自动化框架，覆盖鉴权、异常参数、参数变体、异步任务轮询、结果校验 7 类场景，17 条用例；分层架构（api/services/tests）+ fixture 依赖注入 + 参数化数据驱动
> - 编写 Dockerfile 容器化测试环境，docker-compose 一键部署 Jenkins，保证环境一致性与可复现性
> - 编写 Jenkins Declarative Pipeline 实现持续集成：代码提交自动触发快速测试、手动触发全量用例、HTML 报告归档、失败邮件通知
> - 敏感信息通过 Jenkins Credentials 管理，Token 全程不入代码库
> - 实战解决镜像加速、插件兼容、容器权限、路径转换等 11 类部署问题，沉淀部署排障文档

## 八、后续可扩展方向

- [ ] 配置邮件通知（SMTP + 真实收件人）
- [ ] 与后端确认空 prompt / generateImgCount=0 的校验规则（2 条 negative 用例）
- [ ] GitHub Webhook 接入，实现代码提交自动触发（当前手动触发）
- [ ] 参数化构建（可选跑哪些标记的用例）
- [ ] 构建历史保留策略（丢弃旧构建，防磁盘膨胀）
