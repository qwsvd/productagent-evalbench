# ProductAgent-EvalBench

ProductAgent-EvalBench 是一个面向产品知识库与用户任务的多模型 Agent 上下文工程与评测系统。

## 为什么不是普通聊天机器人

普通聊天机器人主要追求即时对话效果，而本项目关注的是：在明确的产品文档、任务类型、预期要点和风险约束下，验证 Agent 是否能稳定地产生可检查的结构化结果。

换句话说，它不是为了“聊得像人”，而是为了帮助产品、运营和工程团队评估 Agent 在真实产品任务中的可靠性。

## 当前 MVP 支持什么

- 离线运行，不依赖真实模型 API。
- 内置 `MockProvider`，返回稳定的模拟答案。
- 内置 `BaselineAgent`，直接调用 Provider 生成答案。
- 提供 5 份模拟产品文档。
- 提供 20 条产品任务，覆盖产品问答、退款规则、会员权益、账号限制、问题分类和风险控制。
- 提供命令行入口批量运行任务。
- 将完整运行结果写入 `outputs/`。

## 如何运行

建议先安装测试依赖：

```bash
python -m pip install -e ".[dev]"
```

运行 MVP 任务集：

```bash
python -m productagent.cli run --agent baseline --provider mock --task-set product_tasks
```

## 输出结果在哪里

命令运行后会生成：

```text
outputs/baseline_mock_results.jsonl
```

每一行是一条任务的结构化运行结果，包含：

- `task_id`
- `agent`
- `provider`
- `user_query`
- `final_answer`
- `expected_answer_points`
- `risk_points`

## 如何运行测试

```bash
pytest
```

## 下一阶段计划

- RAG：接入产品知识库检索，让 Agent 基于文档片段回答。
- Memory：记录历史任务和用户上下文，支持连续任务。
- Tools：实现可插拔工具接口，例如读取用户状态、查询订单和读取政策。
- Tracing：记录每一步上下文、工具调用和 Provider 输入输出。
- Eval：加入自动评分、人工审查字段和多模型对比报表。