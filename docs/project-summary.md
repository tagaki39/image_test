# 项目成果总结

> 用于简历、面试、绩效汇报的直接素材（2026-08 更新）。

## 一、项目一句话

基于 **pytest + requests** 的 AIGC 图片生成接口自动化测试框架，接入 **Docker 容器化 + Jenkins 持续集成 + 自动登录 + 计费积分校验**，实现从登录到账单的全链路自动化回归。

## 二、技术栈

| 分类 | 技术 |
|------|------|
| 测试框架 | Python / pytest / requests / pytest-html / allure-pytest / pytest-xdist |
| 数据驱动 | YAML（pyyaml） |
| 数据校验 | pydantic / decimal |
| 加密登录 | pycryptodome（AES-256-ECB + RSA PKCS1v1.5） |
| 容器化 | Docker / Docker Compose / Dockerfile |
| CI/CD | Jenkins Declarative Pipeline / HTML Publisher / Allure |
| 版本管理 | Git / GitHub（分支管理） |
| 环境 | Windows + WSL2 / Linux |

## 三、已有功能

### 1. 核心框架（9 类场景，43 条用例）
- 分层架构：`api`（HTTP 封装）→ `services`（业务逻辑）→ `tests`（用例断言）+ `models`（Pydantic 校验）+ `utils`（公共组件）
- fixture 链式注入：`settings → access_token → http_client → image_api/bill_api → services`
- 测试标记体系（smoke / negative / auth / costly / slow / billing），按需选择性执行

### 2. 测试资产（43 条）
| 套件 | 条数 | 覆盖 |
|------|:---:|------|
| 单元测试 | 4 | 状态机（超时/未知状态/失败/成功带错误） |
| 鉴权 | 3 | 无 Token / 过期 Token / 缺 clientid |
| 参数变体 | 17 | 尺寸 3、比例 3、数量 3、模型 5、分辨率 2、genType 2 |
| 异常参数 | 10 | 空/缺失/敏感词/超长 5000 字符/空格/非法格式 |
| 边界值 | 3 | 0 / 负数 / 超上限 |
| 冒烟/提交/失败回调/列表 | 4 | 完整生成链路 |
| 计费 | 2 | 历史账单校验 + E2E 真实计费 |

### 3. 工程化组件
- **统一 HttpClient**：headers 合并、超时、请求/响应记录、401 自动重新认证（重试一次防死循环）
- **Token 生命周期管理**：pytest 启动自动登录（AES+RSA 加密对齐前端），Token 过期 → 401 → 自动重新登录 → 重试原请求
- **通用 TaskPoller**：异步任务轮询组件（图片/视频/音频复用），显式处理进行中/成功/失败/未知状态
- **Pydantic 响应模型**：后端字段类型变化在收集阶段即失败
- **失败现场自动保存**：pytest hook 采集请求/响应（Token 脱敏）到 reports/failures/
- **数据驱动（YAML）**：5 个数据文件，新增用例 = 加数据 + 注释

### 4. 计费积分校验（billing）
- BillService 通用计费组件：账单查询 → taskId 精确匹配 → changeVersion 取最新 → 轮询等待账单 → Decimal 精确校验
- E2E：真实生成任务 → 账单 endCredits == previewCredits > 0，计费字段（model/billingUnit/业务类型）关联校验

### 5. CI/CD
- Jenkins Declarative Pipeline：Checkout → Build Image → Fast Tests → Full Tests（手动触发）→ 双报告归档（pytest-html + Allure）→ 邮件通知
- Docker：测试镜像（含 allure）+ Jenkins 固化镜像（预装 docker CLI）+ compose 一键部署
- 敏感信息：Jenkins Credentials 管理，Token 不入代码库不落镜像

## 四、真实产出（发现的问题）

| 问题 | 说明 |
|------|------|
| 后端参数校验缺口 ×12 | 空/缺失 prompt、敏感词、超长、0/负/超限 count、非法格式均被提交阶段接受（异步才失败） |
| gpt-image-2 模型提交 500 | 后端 "pk is null"，参数不匹配（模型未启用或需额外字段） |
| 鉴权失败返回 HTTP 200+业务 401 | 非标准 HTTP 401 |
| 后端防重 | 相同内容重复提交返回 500"任务重复提交" |
| 登录协议 | Body clientId(大写I)+tenantId，Header clientid(小写)，AES+RSA 加密 |

## 五、简历项目描述

> **AIGC 图片生成接口自动化测试框架**（Python + pytest + Docker + Jenkins）
> - 从零搭建接口自动化框架，覆盖鉴权、异常参数、参数变体、异步任务轮询、失败回调、计费积分校验 9 类场景，43 条用例，YAML 数据驱动
> - 实现 Token 生命周期管理：AES+RSA 加密自动登录 + 401 自动重新认证机制
> - 分层架构（API/Service/Model/Utils）+ 统一 HttpClient + 通用异步任务轮询组件 + Pydantic 响应模型
> - 测试失败自动保存请求/响应现场（Token 脱敏），Allure + pytest-html 双报告
> - 编写 Dockerfile + Jenkins Declarative Pipeline 实现持续集成，凭据安全管理
> - 实战发现并记录后端参数校验缺口 12 项、模型兼容性问题等真实缺陷

## 六、待办

- [ ] 12 条已知失败用例标记 xfail（构建转绿）
- [ ] 合并 feat/bill-credits 到 master
- [ ] Jenkins 凭据同步 LOGIN_* 登录配置
- [ ] 邮件通知 SMTP 配置
- [ ] Playwright E2E（登录→生成→页面结果）
