# API 自动化测试 Agent - Claude Agent SDK 重构设计

## 背景

将原有基于 Anthropic 原始 API 实现的接口自动化测试 Agent，使用 Claude Agent SDK 重写，以学习 SDK 用法并简化代码结构。

## 目标

- 使用 Claude Agent SDK 重写 agent
- 保留 3 个核心工具：read_swagger、write_test_file、run_pytest
- 代码量从 375 行减少到约 150 行
- 全自动执行：输入 Swagger 文件，自动完成全流程

## 项目结构

```
apitest-agent-sdk/
├── .env                    # API Key 配置
├── requirements.txt        # 依赖：claude-agent-sdk
├── agent.py               # 主程序（约 80 行）
├── swagger/               # Swagger 文档目录
│   └── petstore.json      # 示例文档
└── tests/                 # 生成的测试用例目录
```

## 技术方案

### 依赖

```
claude-agent-sdk
pyyaml>=6.0.0
```

### 工具定义

使用 `@tool` 装饰器定义三个核心工具：

```python
from claude_agent_sdk import tool

@tool("read_swagger", "读取 Swagger/OpenAPI 文档，获取接口定义", {
    "file_path": str  # 如 swagger/petstore.json
})
async def read_swagger(args):
    """读取并解析 Swagger 文件（支持 JSON/YAML）"""
    file_path = args["file_path"]
    # 读取文件，返回格式化的 JSON
    return {"content": [{"type": "text", "text": swagger_content}]}


@tool("write_test_file", "将生成的 pytest 测试代码写入文件", {
    "file_name": str,  # 如 test_users.py
    "content": str     # pytest 代码内容
})
async def write_test_file(args):
    """写入测试文件到 tests/ 目录"""
    return {"content": [{"type": "text", "text": "成功：文件已写入"}]}


@tool("run_pytest", "运行 pytest 测试，返回测试结果", {
    "test_file": str   # 可选，不填则运行全部
})
async def run_pytest(args):
    """执行 pytest 并返回输出"""
    return {"content": [{"type": "text", "text": pytest_output}]}
```

### Agent 配置

```python
import anyio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server

# 创建 MCP 服务器（包含所有工具）
server = create_sdk_mcp_server(
    name="api-test-tools",
    version="1.0.0",
    tools=[read_swagger, write_test_file, run_pytest]
)

# 配置 Agent
options = ClaudeAgentOptions(
    system_prompt="""你是一个专业的接口自动化测试 Agent。
    1. 读取 Swagger 文档，理解接口定义
    2. 为每个接口生成 pytest 测试用例
    3. 运行测试并分析结果""",
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__read_swagger", "mcp__tools__write_test_file", "mcp__tools__run_pytest"],
    max_turns=15
)
```

### 主程序（全自动执行）

```python
async def run_agent(swagger_path: str):
    """全自动执行：输入 swagger 路径，自动完成全流程"""
    task = f"读取 {swagger_path}，为所有接口生成 pytest 测试用例，运行测试，如果失败则修复后重试，直到全部通过。"

    async with ClaudeSDKClient(options=options) as client:
        await client.query(task)
        async for message in client.receive_response():
            print(message)

if __name__ == "__main__":
    swagger_file = sys.argv[1]  # python agent.py swagger/petstore.json
    anyio.run(lambda: run_agent(swagger_file))
```

## 代码量对比

| 部分 | 原项目 | SDK 版 |
|------|--------|--------|
| 工具定义 | 123 行 | 40 行 |
| 工具执行器 | 20 行 | 0 行（SDK 自动处理） |
| Agent 循环 | 70 行 | 15 行 |
| 主程序 | 25 行 | 20 行 |
| **总计** | **375 行** | **约 80 行** |

## SDK 优势

1. **@tool 装饰器** - 工具定义从 45 行/工具 减少到 10 行/工具
2. **In-Process MCP Server** - 工具直接在 Python 进程内运行
3. **自动 Agent 循环** - 无需手动处理 stop_reason、tool_use、tool_result
4. **流式输出** - 实时看到 agent 的思考过程
5. **自动上下文管理** - SDK 内部处理对话历史

## 实现步骤

1. 初始化项目：创建 requirements.txt、.env
2. 从原项目复制 swagger/petstore.json 示例文件
3. 实现 agent.py：
   - 导入 SDK
   - 定义 3 个工具
   - 配置 Agent
   - 实现全自动主程序
4. 测试运行

## 参考资料

- [Claude Agent SDK GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
