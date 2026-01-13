# API 自动化测试 Agent

基于 Claude Agent SDK 构建的接口自动化测试 Agent。输入 Swagger 文档，自动完成测试全流程。

## 当前功能

- 读取 Swagger/OpenAPI 文档（JSON/YAML）
- 自动生成 pytest 测试用例
- 运行测试并分析结果
- 测试失败时自动修复并重试

## 使用方法

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key
echo 'ANTHROPIC_API_KEY=sk-ant-xxx' > .env

# 运行 Agent
python agent.py swagger/petstore.json
```

## 项目结构

```
apitest-agent-sdk/
├── agent.py            # Agent 主程序
├── swagger/            # Swagger 文档目录
│   └── petstore.json   # 示例文档
└── tests/              # 生成的测试用例
```

## 后续规划

- [ ] 优化输出显示（精简模式，只显示关键节点）
- [ ] 支持 URL 直接获取 Swagger 文档
- [ ] 支持接口认证（Token、OAuth）
- [ ] 生成测试报告（HTML/JSON）
- [ ] 支持数据库断言
- [ ] 支持环境变量配置（dev/staging/prod）
- [ ] 支持并发测试执行
