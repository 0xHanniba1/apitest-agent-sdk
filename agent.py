"""
接口自动化测试 Agent (Claude Agent SDK 版)
用法: python agent.py swagger/petstore.json
全自动：读取 Swagger -> 生成测试 -> 运行测试 -> 分析结果
"""

import anyio
import json
import subprocess
import os
import sys
from claude_agent_sdk import tool, ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 工具定义
# ============================================================

@tool("read_swagger", "读取 Swagger/OpenAPI 文档，获取接口定义", {
    "file_path": str
})
async def read_swagger(args):
    file_path = args["file_path"]
    full_path = os.path.join(PROJECT_DIR, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if file_path.endswith('.json'):
            data = json.loads(content)
            result = json.dumps(data, indent=2, ensure_ascii=False)
        elif file_path.endswith(('.yaml', '.yml')):
            import yaml
            data = yaml.safe_load(content)
            result = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            result = content
        return {"content": [{"type": "text", "text": result}]}
    except FileNotFoundError:
        return {"content": [{"type": "text", "text": f"错误：文件不存在 - {full_path}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"错误：{str(e)}"}]}


@tool("write_test_file", "将 pytest 测试代码写入文件", {
    "file_name": str,
    "content": str
})
async def write_test_file(args):
    file_name = args["file_name"]
    content = args["content"]
    tests_dir = os.path.join(PROJECT_DIR, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    file_path = os.path.join(tests_dir, file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"content": [{"type": "text", "text": f"成功：{file_path}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"错误：{str(e)}"}]}


@tool("run_pytest", "运行 pytest 测试", {
    "test_file": str
})
async def run_pytest(args):
    test_file = args.get("test_file", "")
    tests_dir = os.path.join(PROJECT_DIR, "tests")
    target = os.path.join(tests_dir, test_file) if test_file else tests_dir
    try:
        result = subprocess.run(
            ["pytest", target, "-v", "--tb=short"],
            capture_output=True, text=True, timeout=60, cwd=PROJECT_DIR
        )
        output = result.stdout + result.stderr
        return {"content": [{"type": "text", "text": output if output else "测试完成"}]}
    except subprocess.TimeoutExpired:
        return {"content": [{"type": "text", "text": "错误：超时"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"错误：{str(e)}"}]}


# ============================================================
# Agent 配置
# ============================================================

server = create_sdk_mcp_server(
    name="api-test-tools",
    version="1.0.0",
    tools=[read_swagger, write_test_file, run_pytest]
)

SYSTEM_PROMPT = """你是一个全自动的接口自动化测试 Agent。

收到 Swagger 文件路径后，自动执行以下流程：
1. 读取 Swagger 文档
2. 分析所有接口
3. 生成 pytest 测试用例
4. 运行测试
5. 如果有失败，分析原因并修复
6. 重新运行直到全部通过（或达到最大重试次数）

测试代码规范：
- 使用 pytest + requests
- 函数命名：test_<接口名>_<场景>
- 包含正常和异常测试用例
"""

options = ClaudeAgentOptions(
    system_prompt=SYSTEM_PROMPT,
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__read_swagger", "mcp__tools__write_test_file", "mcp__tools__run_pytest"],
    max_turns=20
)


# ============================================================
# 主程序 - 全自动执行
# ============================================================

async def run_agent(swagger_path: str):
    """全自动执行：输入 swagger 路径，自动完成全流程"""
    print(f"\n{'='*60}")
    print(f"API 自动化测试 Agent")
    print(f"输入: {swagger_path}")
    print(f"{'='*60}\n")

    task = f"读取 {swagger_path}，为所有接口生成 pytest 测试用例，运行测试，如果失败则修复后重试，直到全部通过。"

    async with ClaudeSDKClient(options=options) as client:
        await client.query(task)
        async for message in client.receive_response():
            print(message)

    print(f"\n{'='*60}")
    print("Agent 执行完成")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python agent.py <swagger文件路径>")
        print("示例: python agent.py swagger/petstore.json")
        sys.exit(1)

    swagger_file = sys.argv[1]
    anyio.run(lambda: run_agent(swagger_file))
