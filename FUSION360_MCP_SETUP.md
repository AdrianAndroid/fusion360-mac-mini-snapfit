# Autodesk Fusion 360 MCP：从安装到验证成功

本文记录在 macOS 上安装并验证 `faust-machines/fusion360-mcp-server` 的正确流程，供后续 AI 或维护人员复用。

## 1. 环境与路径

本次验证环境：

- Fusion：`/Users/zhaojian/Applications/Autodesk Fusion.app`
- Claude Code：`2.1.295`
- Python：`3.12.7`
- uv / uvx：`0.11.24`
- uvx 绝对路径：`/Users/zhaojian/.local/bin/uvx`
- MCP 源码：`/Users/zhaojian/code/fusion360/fusion360-mcp-server`
- Fusion 插件目录：`/Users/zhaojian/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/Fusion360MCP`
- 插件日志：`/Users/zhaojian/fusion360mcp.log`
- 本地桥接地址：`127.0.0.1:9876`

开始前确认 Python 3.10 或更高版本、Claude Code、uv/uvx 和 Fusion 均已安装。

## 2. 下载 MCP 源码

将源码克隆到独立目录：

```bash
git clone "https://github.com/faust-machines/fusion360-mcp-server.git" \
  "/Users/zhaojian/code/fusion360/fusion360-mcp-server"
```

检查源码状态和插件文件：

```bash
git -C "/Users/zhaojian/code/fusion360/fusion360-mcp-server" status --short
git -C "/Users/zhaojian/code/fusion360/fusion360-mcp-server" log -1 --oneline
find "/Users/zhaojian/code/fusion360/fusion360-mcp-server/addon" \
  -maxdepth 2 -type f -print
```

插件目录必须包含：

```text
addon/Fusion360MCP.manifest
addon/Fusion360MCP.py
addon/server/
```

本次验证的源码提交为 `19b9f1e`。使用该本地源码启动 MCP Server，可由其 `pyproject.toml` 中的 `mcp>=1.0,<2` 约束安装兼容的 MCP SDK。

## 3. 安装 Fusion 插件

确认目标不存在后，将 `addon` 整体复制为 `Fusion360MCP`：

```bash
test ! -e "/Users/zhaojian/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/Fusion360MCP" && \
mkdir -p "/Users/zhaojian/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns" && \
ditto "/Users/zhaojian/code/fusion360/fusion360-mcp-server/addon" \
  "/Users/zhaojian/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/Fusion360MCP"
```

验证源目录与安装目录一致：

```bash
diff -r \
  "/Users/zhaojian/code/fusion360/fusion360-mcp-server/addon" \
  "/Users/zhaojian/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/Fusion360MCP"
```

`diff` 无输出即表示一致。安装后目录层级应为：

```text
Fusion360MCP/
├── Fusion360MCP.manifest
├── Fusion360MCP.py
└── server/
```

## 4. 注册 Claude Code MCP Server

使用本地源码和 uvx 的绝对路径进行用户级注册：

```bash
claude mcp add --scope user fusion360 -- \
  /Users/zhaojian/.local/bin/uvx \
  --from "/Users/zhaojian/code/fusion360/fusion360-mcp-server" \
  fusion360-mcp-server --mode socket
```

检查注册信息和连接状态：

```bash
claude mcp get fusion360
claude mcp list
```

正确结果应包含：

```text
Scope: User config
Status: ✔ Connected
Type: stdio
Command: /Users/zhaojian/.local/bin/uvx
Args: --from /Users/zhaojian/code/fusion360/fusion360-mcp-server fusion360-mcp-server --mode socket
```

首次启动由 uvx 安装依赖；依赖已缓存后，后续启动会直接复用。

## 5. 在 Fusion 中启动插件

1. 打开 Fusion，并新建或打开一个 Design 文档。
2. 按 `Shift+S` 打开“脚本和附加模块”。
3. 进入“附加模块 / Add-Ins”。
4. 找到 `Fusion360MCP`，版本为 `0.1.0`。
5. 点击该行左侧开关，使其变为蓝色，启动插件。
6. 初次验证期间不必勾选“启动时运行”；验证成功后可按需要启用。

检查本地监听：

```bash
lsof -nP -iTCP:9876 -sTCP:LISTEN
```

正确结果应类似：

```text
Autodesk  ...  TCP 127.0.0.1:9876 (LISTEN)
```

检查日志：

```bash
cat "/Users/zhaojian/fusion360mcp.log"
```

应包含：

```text
Fusion360MCP loaded - server on localhost:9876
Server listening on localhost:9876
```

保持监听地址为本机回环地址。该桥接没有身份认证，不要设置 `FUSION_MCP_HOST=0.0.0.0`，也不要将端口暴露到公共网络。

## 6. 让 Claude Code 加载新工具

新注册的 MCP 工具通常需要重启 Claude Code 会话后才会注入：

1. 保持 Fusion 和 Fusion360MCP 插件运行。
2. 退出当前 Claude Code。
3. 在原工作目录运行：

```bash
claude --continue
```

如果当前客户端已经加载 Fusion 工具，直接调用：

1. `ping`
2. `get_scene_info`

`ping` 预期返回 `status: pong`；`get_scene_info` 应返回当前 Design 的名称、实体、草图、特征和相机信息。

## 7. 使用官方 MCP Python 客户端验证

本地验证脚本位于：

```text
/Users/zhaojian/code/fusion360/verify_fusion_mcp_connection.py
```

该脚本使用与 Claude 注册信息相同的 uvx 启动命令，通过官方 MCP Python SDK 建立 stdio 会话，并依次调用 `ping` 和 `get_scene_info`。

运行方式：

```bash
/Users/zhaojian/.local/bin/uv run --no-project --with 'mcp<2' \
  python -I "/Users/zhaojian/code/fusion360/verify_fusion_mcp_connection.py"
```

本次验证成功的关键输出为：

```text
=== ping ===
**ping** OK
  status: pong

=== get_scene_info ===
**get_scene_info** OK
  design_name: 无标题
  bodies_count: 0
  sketches_count: 0
  features_count: 0
```

看到以上结果即表示完整链路可用：

```text
MCP 客户端
  → uvx stdio MCP Server
  → 127.0.0.1:9876
  → Fusion360MCP 插件
  → 当前激活的 Fusion Design
```

## 8. 成功判定与后续注意事项

全部满足以下条件即安装验证完成：

- `claude mcp list` 中 `fusion360` 为 `✔ Connected`。
- Fusion 插件已启动，`127.0.0.1:9876` 正在监听。
- `ping` 返回 `pong`。
- `get_scene_info` 能读取当前 Design。

后续建模时注意：

- Fusion API 的内部长度单位是厘米；如果设计要求是毫米，调用工具前必须核对参数单位并正确换算。
- 修改模型前确认当前激活的是目标 Design。
- 如果源码目录被移动，需同步更新 Claude 的 MCP 注册路径。
- 更新源码后，如需更新 Fusion 插件，应重新复制 `addon`；本次安装使用的是目录副本，不是符号链接。
