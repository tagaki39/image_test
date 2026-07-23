# 本次修改

- 新增 `GET /prod-api/aigc/task/{taskId}` 任务详情接口封装。
- 完整生成流程改为直接按任务 ID 轮询详情，不再遍历任务列表。
- 保留 `resourceTaskList`，仅用于历史列表和分页结构测试。
- 增加任务详情 ID 一致性、业务字段、资源关联 taskId 等断言。
- 更新 README 使用说明。
- 已通过 `python -m compileall` 和 `pytest --collect-only`，共收集 8 条测试。
