# 图片生成接口自动化框架

基于 `pytest + requests`，覆盖：

- 图片生成任务提交
- 任务ID提取
- 任务详情接口轮询
- 成功/失败状态判断
- 结果图片URL校验
- 参数异常测试
- 鉴权测试
- HTML测试报告

## 已确认接口

### 提交图片任务

```http
POST /prod-api/aigc/task/generateImage
```

成功响应示例：

```json
{
  "code": 200,
  "msg": "成功",
  "data": "2077691650588999682"
}
```

### 按任务ID查询详情（用于轮询）

```http
GET /prod-api/aigc/task/{taskId}
```

提交接口返回任务ID后，框架会每隔指定时间直接查询该任务详情，直到成功、失败或超时。

### 查询图片任务列表（独立列表测试）

```http
GET /prod-api/aigc/task/resourceTaskList
```

参数：

```text
businessType=1
pageNum=1
pageSize=5
```

该接口仅用于验证历史任务列表、分页和字段结构，不再用于任务状态轮询。

当前已确认：

```text
status = 3：生成成功
status = 4：生成失败
```

## 一、安装

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

Linux / macOS：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 二、配置

复制配置模板：

```bash
copy .env.example .env
```

Linux / macOS：

```bash
cp .env.example .env
```

修改 `.env`：

```env
BASE_URL=https://test.xywhaigc.top
AUTHORIZATION=Bearer 你的最新Token
CLIENT_ID=你的clientid
REFERENCE_IMAGE_URL=一张长期可访问的测试图片URL
```

不要把 `.env` 提交到 Git。

## 三、运行

运行全部测试：

```bash
pytest
```

只运行冒烟：

```bash
pytest -m smoke
```

排除真实AI生成用例：

```bash
pytest -m "not costly"
```

只运行鉴权：

```bash
pytest -m auth
```

生成HTML报告：

```bash
pytest --html=reports/report.html --self-contained-html
```

并行运行非生成类用例：

```bash
pytest -n auto -m "not costly"
```

不建议并行大量执行真实图片生成请求，以免产生费用、限流或污染测试数据。

## 四、目录说明

```text
image_api_pytest_framework/
├─ api/
│  └─ image_api.py
├─ services/
│  └─ image_task_service.py
├─ utils/
│  ├─ assertions.py
│  └─ config.py
├─ data/
│  ├─ payloads.py
│  ├─ image_invalid_cases.json   # 异常参数（空/缺失/敏感词/非法格式）
│  ├─ boundary_cases.json        # 边界值（0/负数/超上限）
│  ├─ image_valid_cases.json     # 合法参数变体（尺寸/比例/数量）
│  └─ auth_cases.json            # 鉴权失败场景
├─ models/                       # Pydantic 响应模型
├─ tests/
│  ├─ test_auth.py
│  ├─ test_image_generate_negative.py
│  ├─ test_image_generate_params.py
│  ├─ test_image_generate_smoke.py
│  ├─ test_image_generate_submit.py
│  ├─ test_image_generate_failure.py
│  ├─ test_task_list.py
│  └─ test_task_service_unit.py
├─ docker/
│  └─ jenkins.Dockerfile     # 固化 Jenkins 镜像（预装 docker CLI）
├─ docker-compose.yml        # 一键启动 Jenkins
├─ Jenkinsfile               # CI 流水线
├─ Dockerfile                # 测试镜像
├─ conftest.py
├─ pytest.ini
├─ requirements.txt
├─ .env.example
└─ README.md
```

## 五、CI/CD（Jenkins + Docker）

### 流水线结构

```
代码提交/手动触发
  → Build Test Image     构建测试镜像（Dockerfile，python:3.12-slim）
  → Fast Tests           非生成类用例（pytest -m "not costly"，秒级）
  → Full Tests           全量用例（仅手动触发，含真实 AI 生成）
  → HTML 报告归档 × 2     pytest-html + HTML Publisher
  → 邮件通知             构建结果发送（emailext）
```

### 本地 Docker 跑测试

```bash
docker build -t image-api-test .
docker run --rm --env-file .env image-api-test            # 非生成类
docker run --rm --env-file .env image-api-test pytest      # 全量
```

### 一键部署 Jenkins

```bash
docker build -f docker/jenkins.Dockerfile -t jenkins-ci:1.0 .
docker compose up -d
# 浏览器打开 http://localhost:8080（初始密码：docker logs jenkins）
```

完整部署与排障手册见 [docs/jenkins-docker-setup.md](docs/jenkins-docker-setup.md)。

## 六、重要说明

1. AI生成结果具有随机性，不应断言生成图片内容完全一致。
2. 推荐断言任务状态、字段结构、图片URL、图片可访问性、尺寸和数量。
3. 完整生成流程使用 `GET /prod-api/aigc/task/{taskId}` 直接轮询任务详情，不受列表分页影响。
4. 参数异常用例中的精确预期码需要结合接口文档或后端规则继续完善。
5. Token过期后更新 `.env` 即可。
