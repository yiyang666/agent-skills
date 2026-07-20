---
name: work-cloud-doc-publisher
description: 把模块 README.md / TEST_GUIDE.md 等本地 Markdown 发布到钉钉或飞书云文档。默认钉钉 Workspace、固定父目录与标题映射；同名默认新建避免覆盖。不负责写文档、不批量迁移、不改共享权限。
---

# 工作云文档发布

用本机官方 CLI（钉钉 `dws` / 飞书 `lark-cli`）发布本地 Markdown。**禁止猜命令**；参数以本机 Skill + `--help` 为准。目标：少确认、短链路、低 token。

## 默认约定（用户未指定时直接用，交付结果里写明）

| 项 | 默认 |
|---|---|
| 平台 | **钉钉**（仅当用户明确说飞书/都发布时才换） |
| Workspace | 钉钉「我的文档」：`dws wiki space list --type myWikiSpace` |
| 父目录 | **`模块设计与测试说明`**（在 Workspace 下查找；不存在则询问，勿猜别的根） |
| 子文件夹 | 用户指定；否则用模块显示名（用户指定 → README 中文定位 → 目录名） |
| 源文档 | 用户 `@` 的路径；若只给模块目录则发 `README.md` + `TEST_GUIDE.md`（各一篇，不合并） |
| 同名策略 | **始终新建**；只有用户明确说「更新同名/覆盖」才 update |
| 必问 | 仅：平台非默认且未指定、父目录找不到且无法唯一创建、目标文件夹同名不唯一、用户只说预览未授权写入 |

### 云文档标题映射

| 本地文件 | 默认标题 |
|---|---|
| `README.md`（或模块 README） | `{模块显示名}设计说明` |
| `TEST_GUIDE.md` | `{模块显示名}测试说明` |
| 其他 `*.md` | 首个 H1；无则文件名（去扩展名） |

用户给出的标题优先于上表。

## 最小阅读（按任务，勿通读全部官方 Skill）

| 任务 | 钉钉 | 飞书 |
|---|---|---|
| 认证 | `dws-shared` 认证段 + `dws auth status` | `lark-shared` + `lark-cli auth status` |
| 找/建文件夹 | `dingtalk-wiki`（node list/create） | 需要时再读 `lark-drive` |
| 写/回读文档 | `dingtalk-doc`（create/read；update 仅用户要求覆盖时） | `lark-doc` |
| 按名搜索 | `dingtalk-drive` 的 `drive search`（可选） | `lark-drive` 搜索 |

参数不确定时对该子命令跑一次 `--help` / `dws schema "<path>" --compact`，不要把整份 help 贴进上下文。

## CLI 与 PATH

详见 [platform-routing.md](references/platform-routing.md)。

- 查 CLI 前：`export PATH="$HOME/.local/bin:$PATH"`（`dws` / 部分工具常装在此）。
- `command -v dws` 或 `lark-cli` 失败再报缺失；不要先全盘 find。

## 钉钉主路径（推荐，短链路）

```text
1. PATH 加上 ~/.local/bin → dws auth status --format json
2. wiki space list --type myWikiSpace → workspaceId
3. drive search / wiki node list 定位父目录「模块设计与测试说明」→ parentNodeId
4. 子文件夹：wiki node list 查找；没有则
   dws wiki node create --workspace <WS> --folder <父> --name "<子>" --type folder
5. 每篇：dws doc create --name "<标题>" --folder <子文件夹nodeId> --content-file <本地.md> --format json
6. 回读：doc read 取 title + 正文前 ~200 字；wiki node list 确认两篇都在
7. 输出结果表
```

### 钉钉铁律（P0）

- **建文档父目录只用** `dws wiki node create ... --type folder`。
- **禁止**用 `dws drive mkdir` 的结果当作 `doc create --folder`：钉盘文件夹常导致 `RESOURCE_NOT_FOUND`。
- `doc create` 的 `--folder` 必须是 **wiki/文档空间** 的 nodeId（或文档文件夹 URL），不要传纯钉盘 dentry。

飞书：按 `lark-doc` / `lark-drive` 本机说明建目录与文档；不套用上述钉钉 wiki 命令。

## 精简工作流

### 1. 本地校验（轻量）

- 路径存在、非空；记下相对路径与将用标题。
- **不做**全量相对图片扫描；用户或内容明确依赖本地图时，在结果里一句提示即可。
- **不强制**内容哈希；需要防重复时可选。

### 2. 认证

只读状态命令；未登录则停止并给出官方登录步骤。不扩大权限、不打印 Token。

### 3. 计划与执行

- 用户已说「发布/推送」且默认足够时：**直接执行**，结果表注明所用默认。
- 仍须先问：父目录缺失且同名不唯一、用户只要预览。
- 按「源文档逐篇」创建；`都发布` 时一平台失败不回滚另一平台。
- Mermaid：保留代码块；平台不渲染时在结果中提示，不擅自转图。
- 回读只做标题 + 短摘要，勿全文灌进对话。

### 4. 错误

| 错误 | 处理 |
|---|---|
| 未登录 | 停止 + 官方 login |
| 权限不足 | 停止 + 最小权限说明 |
| 未知命令/flag | 读 `--help` 修正一次 |
| 限流/网络 | 退避，最多 2 次 |
| 目标不唯一 | 停止并请用户选 |
| `doc create` + drive 文件夹 | 改用 wiki 文件夹 nodeId 重试一次，勿再 drive mkdir |

### 5. 交付

| 平台 | 源文件 | 动作 | 目标文件夹 | 云文档标题 | 状态 | 链接/错误 |
|---|---|---|---|---|---|---|

附：成功/失败数、是否用了默认标题或目录、下次仍为「新建」还是「更新」、Mermaid 等降级说明。

## 安全边界

- 不删云文档、不改共享、不通知他人，除非用户明确要求。
- 不读无关云文档；不发到用户未指定的平台或个人空间以外的目标。
- **不修改本地源文档**。
