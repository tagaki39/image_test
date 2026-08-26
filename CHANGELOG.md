# 变更记录

## 2026-08-26 第二批工程化：HttpClient + 401 自动重试 + Pydantic 模型

### 改动

- 新增 `utils/http_client.py`：统一请求客户端（headers 合并、超时、请求/响应记录、401 自动重新认证）
- 新增 `models/`：Pydantic 响应模型（TaskDetail / LoginResponse），后端字段类型变化时收集阶段即失败
- `api/` 层改造：ImageApi / AuthApi 全部基于 HttpClient，删除各自重复的请求/记录逻辑
- `conftest.py`：`http_client` fixture 携带 401 刷新回调（自动重新登录，仅重试一次防死循环）
- 新增依赖：`pydantic>=2.7`

### 遇到的问题与解决

| 问题 | 根因 | 解决 |
|------|------|------|
| 401 重试后仍 401 | 重试请求沿用第一次构造的旧 headers，session 中已更新的新 Token 未生效 | 重试前重新合并 session.headers（含新 Token） |
| `retry_auth` 参数丢失 | HttpClient.post() 未透传到 request() | post() 增加 retry_auth 透传 |
| 登录接口误触发 401 重试 | 登录失败（如密码错）返回 401 会递归调用登录 | 登录请求显式 `retry_auth=False` |

### 改动前后对比

| 维度 | 改动前 | 改动后 |
|------|--------|--------|
| Token 过期处理 | 每次手动更新 .env / Jenkins 凭据，过期后所有用例 401 失败 | 401 → 自动重新登录 → 更新 Session → 重试原请求，全程无感 |
| 请求公共逻辑 | ImageApi / AuthApi 各自写 requests 调用、记录、超时处理 | 统一收拢到 HttpClient，API 层重复代码减少约 40% |
| 响应字段校验 | `.get()` + assert，字段类型变化要等断言阶段才发现 | Pydantic 模型校验，收集阶段即失败并给出明确字段错误 |
| 登录失败处理 | 登录失败可能递归触发 401 重试 | 登录请求显式 `retry_auth=False`，防递归 |

## 2026-08-26 第一批工程化：状态枚举 + 失败现场 + 数据驱动

### 改动

- 新增 `utils/enums.py`：TaskStatus / BusinessCode 枚举，Service 与测试魔法值全部替换
- 新增 `utils/recorder.py` + conftest hook：测试失败自动保存请求/响应现场到 `reports/failures/`（Authorization 脱敏）
- 新增 `data/param_variants.json`：参数变体数据驱动化，变体列表改 JSON，加用例不改代码

### 改动前后对比

| 维度 | 改动前 | 改动后 |
|------|--------|--------|
| 状态可读性 | `status == 3` 魔法值散落 | `status == TaskStatus.SUCCESS`，语义自明 |
| CI 失败定位 | 看日志猜请求内容，必要时重跑 | `reports/failures/` 自动保存完整请求/响应 JSON（Token 脱敏），无需重跑 |
| 增加参数变体 | 改测试代码里的列表 | 改 `param_variants.json`，零代码改动 |

## 2026-08-25 自动登录

- 新增 `api/auth_api.py`：AES-256-ECB+PKCS7 加密请求体，RSA PKCS1v1.5 加密 AES key（对齐前端 CryptoJS）
- 新增 `services/auth_service.py`：登录业务 + access_token 校验
- conftest 自动登录链：`auth_api → access_token → http_client`，未配置登录信息时回退静态 Token
- 实测后端要求：Body `clientId`（大写 I）+ `tenantId=000000`，Header `clientid`（小写）

## 历史（早期）

- 新增 `GET /prod-api/aigc/task/{taskId}` 任务详情接口封装。
- 完整生成流程改为直接按任务 ID 轮询详情，不再遍历任务列表。
- 保留 `resourceTaskList`，仅用于历史列表和分页结构测试。
- 增加任务详情 ID 一致性、业务字段、资源关联 taskId 等断言。
- 更新 README 使用说明。
