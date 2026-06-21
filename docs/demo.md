# AI MCP Gateway 标准演示流程

这份文档用于面试或项目展示时按固定顺序演示系统能力。目标是展示“服务注册 -> 工具发现 -> 网关鉴权路由 -> Agent 工具调用 -> 日志与统计”的闭环。

## 0. 准备

需要三个终端：

```bash
# Terminal 1: MCP Server
cd /Users/yizhou/code/python_project/ai-mcp-gateway/services/real_mall_mcp
./venv/bin/python main.py
```

```bash
# Terminal 2: Backend
cd /Users/yizhou/code/python_project/ai-mcp-gateway
./venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
# Terminal 3: Frontend
cd /Users/yizhou/code/python_project/ai-mcp-gateway/frontend
npm run dev -- --host 127.0.0.1 --port 3000
```

访问：

```text
http://localhost:3000
```

## 1. 注册 MCP 服务

进入“微服务管理”，添加服务：

- 服务名称：`real-mall-mcp`
- 服务地址：`http://127.0.0.1:5001`
- 描述：`拼团商城 MCP 演示服务`

保存后，系统会尝试同步工具。若工具数量为 0，进入详情页点击“同步工具”或“健康检查”。

预期结果：

- 服务状态为 `online`。
- 工具数量大于 0。
- 工具管理页能看到 `list_active_group_buy_activities`、`analyze_activity_sales`、`find_unfinished_teams` 等工具。

## 2. 创建 API Key

进入“网关管理 -> API Key 管理”，创建一个 Key：

- 名称：`demo-key`
- 权限：勾选 `read` 和 `write`
- 过期时间：可留空

复制创建后显示的完整 API Key。关闭弹窗后完整 Key 不会再次展示。

## 3. 配置路由规则

进入“网关管理 -> 路由规则”，新增规则：

- 路径模式：`/mall/*`
- 目标微服务：`real-mall-mcp`
- 优先级：`10`

这表示访问 `/gateway/mall/...` 的请求会被路由到拼团商城 MCP 服务。

## 4. 验证网关入口

将下面命令中的 `YOUR_API_KEY` 换成刚创建的 Key。

```bash
curl -X POST http://127.0.0.1:8000/gateway/mall/tools \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'
```

预期结果：

- 返回 JSON-RPC 响应。
- `result.tools` 中包含已同步的 MCP 工具。

工具调用示例：

```bash
curl -X POST http://127.0.0.1:8000/gateway/mall/tools \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "analyze_activity_sales",
      "arguments": {"activity_id": 100123}
    }
  }'
```

预期结果：

- 返回 `result.content`。
- Dashboard 的工具调用排行会更新。

## 5. 演示 Agent 对话测试

进入“对话测试”：

- 填写 LLM API Key。
- 填写模型名。
- 如使用兼容 OpenAI 的第三方服务，填写 Base URL。
- 选择 `real-mall-mcp` 服务。
- 点击“连接并开始测试”。

可提问：

```text
帮我分析当前拼团活动的运营情况：哪些活动效果最好，哪些商品卖得好，有哪些未成团队伍需要关注？
```

或：

```text
查看 100123 这个拼团活动的详情，并分析它的销售表现。
```

预期结果：

- 页面显示用户消息。
- AI 如果需要工具，会显示工具调用卡片。
- 卡片中包含工具名、参数、结果和耗时。
- 最终显示模型整理后的回答。

## 6. 展示工具管理边界

进入“工具管理”，打开任意工具详情。

预期结果：

- 页面只展示工具名称、描述、状态和参数 Schema。
- 可以启停或删除已同步工具记录。
- 不提供在线编辑 Python 函数体、写入源码或重启 MCP 服务的入口。

这可以用来说明项目把工具管理边界收敛为“发现、查看、启停、删除”，真正的工具实现仍由 MCP 服务自身维护。

## 7. 展示测试与工程质量

```bash
cd /Users/yizhou/code/python_project/ai-mcp-gateway
./venv/bin/python -m unittest discover backend/tests -v
```

当前测试覆盖：

- 缺少 Bearer Token 时网关拒绝请求。
- 授权后网关按路由调用目标 MCP 服务。
- 健康检查失败会标记服务 offline。
- 健康检查成功会同步工具。
- 危险的工具部署接口不再暴露。
- 聊天接口会创建会话、保存消息、传递历史上下文。
- `real-mall-mcp` 拼团业务工具只读取真实 `group_buy_market` 数据库。
