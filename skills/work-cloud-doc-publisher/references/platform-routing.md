# 平台路由与发现

## 目标

让 Agent 快速定位飞书与钉钉官方 CLI/Skills，并始终以本机安装版本的说明为准，避免猜命令、重复搜索和无意义工具尝试。

## 标准查找顺序

只检查下列位置：

1. 当前项目 `.cursor/skills/`
2. Cursor 用户目录 `~/.cursor/skills/`
3. 通用用户目录 `~/.agents/skills/`
4. 当前 Agent 明确暴露的已安装 Skills 列表

软链接可以用于多个 Agent 共享同一份 Skill，但执行前解析真实路径，并确认它仍位于可信的 Skill 根目录。不要复制同一官方 Skill 的多个版本到不同目录。

## 飞书

官方来源：`https://github.com/larksuite/cli`

官方可执行文件：`lark-cli`

本流程需要的官方 Skills：

- `lark-shared`：认证、身份、权限和安全规则，必须先读。
- `lark-doc`：创建、读取、更新和搜索飞书文档。
- `lark-drive`：查找目录、管理文件夹、权限和评论。
- `lark-markdown`：仅当目标明确是飞书云盘原生 Markdown 文件时使用，不替代普通飞书文档。

推荐预检：

```bash
command -v lark-cli
lark-cli auth status
lark-cli docs --help
```

发布普通飞书文档时，先读取已安装的 `lark-shared/SKILL.md` 与 `lark-doc/SKILL.md`。涉及目标目录时再读取 `lark-drive/SKILL.md`。命令形状以这些文件和当前 `--help` 为准。

官方仓库在 2026-07-17 展示的 Markdown 创建快捷方式属于 `lark-cli docs +create`，但不要把网页示例当作本机版本的固定接口；仍须先读取本机 Skill。

## 钉钉

官方来源：`https://open.dingtalk.com/dingtalk-cli`

官方可执行文件：`dws`（DingTalk Workspace CLI）。

推荐预检：

```bash
command -v dws
dws --help
```

钉钉官方 CLI 会向 Cursor 等 Agent 安装结构化 Skills。由于 Skill 名称和子命令可能随版本调整，应在标准 Skill 目录中筛选 frontmatter 或描述同时包含“钉钉/DingTalk”和“文档/云盘/知识库”的官方 Skill，再读取其 `SKILL.md`。不得仅凭关键词猜测一个不存在的命令。

若筛选到多个候选，选择规则依次为：

1. 能创建/更新普通云文档。
2. 能解析或创建目标文件夹。
3. 明确支持 Markdown 输入。
4. 与当前 `dws --help` 输出一致。

## 缺失时的处理

- CLI 缺失：报告可执行文件名与官方来源，停止该平台任务。
- CLI 存在但 Skill 缺失：报告标准查找位置和官方安装入口，停止任务。
- 版本不一致：使用本机 Skill 和 `--help`，不要自动升级。
- 用户要求安装/升级：先扫描完整候选 Skill，安全门通过后再安装；不要在发布任务中顺手安装。

## 选择原则

- 普通文档优先平台文档 Skill，目录定位再调用云盘/Drive Skill。
- 不使用浏览器模拟点击替代可用的官方 CLI。
- 不绕过官方 Skill 直接拼接未经确认的 OpenAPI 请求。
- 对同一平台只保留一个明确的官方命令链，避免并行尝试多个写入接口造成重复文档。
