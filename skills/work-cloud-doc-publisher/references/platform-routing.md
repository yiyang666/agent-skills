# 平台路由与发现

目标：快速找到 CLI/Skill，短预检，不猜命令、不全盘搜索。

## PATH

执行任何 `dws` / `lark-cli` 前先保证：

```bash
export PATH="$HOME/.local/bin:$PATH"
command -v dws || command -v lark-cli
```

`dws` 常见安装位置：`~/.local/bin/dws`。PATH 未包含时会被误判为「未安装」。

## Skill 查找（仅这些位置）

1. 项目 `.cursor/skills/`
2. `~/.cursor/skills/`
3. `~/.agents/skills/`
4. 当前 Agent 已暴露的 Skills 列表

不递归搜索整个 `$HOME`。软链接解析到真实路径后须仍在可信 Skill 根下。

## 飞书

- 来源：`https://github.com/larksuite/cli`
- 二进制：`lark-cli`
- 最小阅读：`lark-shared`（认证）→ `lark-doc`（写文档）；目录再读 `lark-drive`
- 预检：`lark-cli auth status`；命令以本机 Skill + `--help` 为准

## 钉钉

- 来源：`https://open.dingtalk.com/dingtalk-cli`
- 二进制：`dws`
- 最小阅读：`dws-shared`（认证）→ `dingtalk-wiki`（文件夹）→ `dingtalk-doc`（正文）；按名搜索再用 `dingtalk-drive`
- 预检：

```bash
export PATH="$HOME/.local/bin:$PATH"
dws auth status --format json
```

### 钉钉文件夹 vs 钉盘（必读）

| 用途 | 应用 |
|---|---|
| 作为 `doc create --folder` 的父节点 | **仅** `dws wiki node create --type folder`（或已有 wiki 文件夹 nodeId） |
| 钉盘文件上传/下载 | `dws drive …` |
| **禁止** | 用 `dws drive mkdir` 的 fileId 当文档父目录（常触发 RESOURCE_NOT_FOUND） |

定位「模块设计与测试说明」等目录：优先 `drive search --query` 或 `wiki node list`；确认返回项带 `workspaceId` / 可作为文档文件夹的 `nodeId`。

## 缺失时

- CLI 不在 PATH（含补上 `~/.local/bin` 后仍无）：报告官方来源，停止该平台。
- CLI 有、Skill 无：报告标准查找位置，停止；发布任务中不擅自安装。
- 版本漂移：以本机 Skill + `--help` 为准，不自动升级。

## 原则

- 一条官方写入链走到底；失败按 SKILL 错误表处理，不并行多套 create 接口以免重复文档。
- 不用浏览器点击代替可用 CLI。
- 不绕过官方 Skill 手搓未确认的 OpenAPI。
