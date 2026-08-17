---
name: learn-engineering-postmortem
description: 把开发中的经典问题、缺陷复盘与设计洞见整理成结构化 Markdown，并默认发布到钉钉「工程设计复盘」目录。用于知识沉淀、面试材料与团队复盘。Use when 用户要求总结经典 bug/设计问题、写复盘文档、沉淀到钉钉、整理面试故事，或提到 postmortem/知识沉淀/工程复盘。不负责日常模块 README/TEST_GUIDE（走 work-module-docs），不负责无分析地只转发已有 Markdown（走 work-cloud-doc-publisher）。
---

# 工程设计复盘沉淀

将一次「问题 → 根因 → 方案 → 原理 → 发散」整理成可复用的钉钉文档，并沉淀为个人知识。

## 何时使用

- 用户明确要求：复盘 / 知识沉淀 / 面试材料 / 经典问题总结
- 刚完成一次高价值修复或架构取舍，需要固化学习点
- 用户希望「以后这类事都按同样流程沉淀」

不要用本 Skill：

- 只生成模块设计/测试说明 → `work-module-docs`
- 已有定稿 Markdown，仅上传云文档 → `work-cloud-doc-publisher`

## 默认约定

| 项 | 默认 |
|---|---|
| 平台 | 钉钉 |
| Workspace | 我的文档（`dws wiki space list --type myWikiSpace`） |
| 目标文件夹 | **`工程设计复盘`**（位于「我的文档」根下；不存在则创建） |
| 同名策略 | 始终新建；仅用户说「更新/覆盖」时 update |
| 本地稿 | 先写临时 `.md`，再用 `dws doc create --content-file` |
| 发布 | 用户说「沉淀到钉钉/建钉钉文档」即视为授权写入 |

发布编排复用 `work-cloud-doc-publisher` 的钉钉短链路与铁律（wiki 文件夹 nodeId，禁止 `drive mkdir` 当 `doc create --folder`）。认证与命令发现先读 `dws-shared`。

## 工作流

```text
1. 收集材料：现象、复现、相关代码路径、已采用方案、未做项
2. 按模板写本地 Markdown（见 references/postmortem-template.md）
3. 自检：根因是否可证伪；方案是否对应根因；发散是否可迁移
4. 发布钉钉：定位/创建「工程设计复盘」→ doc create → doc read 回读
5. 交付：标题、链接、一句话结论；可选建议后续面试口述稿
```

### 写作原则

- **先结论后细节**；面试可用段落单独成节。
- **区分主因与强化因素**（例如瞬时归零放大丢停包，但不是租约缺失本身）。
- **方案分层**：P0 安全兜底 / P1 正确性 / P2 纵深，避免一把梭。
- **发散要可迁移**：写成检查清单或默认问题（“发送端死了会怎样？”），少写口号。
- **脱敏**：不写 Token、内网地址、账号密码、未公开漏洞利用细节。
- 代码引用点到模块/接口即可，不必贴大段实现。

### 必问（仅这些）

- 目标文件夹 `工程设计复盘` 找不到且无法唯一创建
- 目标文件夹同名不唯一
- 用户只要本地稿、明确不要发布

## 文档结构（必须覆盖）

1. 问题背景（现象 + 旧架构为何失败）
2. 解决方案总览（一张表或一句话闭环）
3. 关键手段原理 + 各解决什么问题
4. 发散：后续哪些设计要同样考虑
5. （可选）面试 60–90 秒口述稿、参数备忘、暂缓项

详细标题与段落提示见 [postmortem-template.md](references/postmortem-template.md)。  
质量对照见 [quality-checklist.md](references/quality-checklist.md)。

## 钉钉发布短链路

```text
PATH += ~/.local/bin
dws auth status --format json
wiki space list --type myWikiSpace → workspaceId
在「我的文档」根下定位「工程设计复盘」
  （wiki node list / node search）；没有则
  wiki node create --workspace <WS> --name "工程设计复盘" --type folder
doc create --name "<标题>" --folder <工程设计复盘nodeId> --content-file <md> --format json
doc read 回读标题 + 正文前约 200 字
```

标题优先用用户指定；否则用文稿首个 H1。

## 交付格式

| 项 | 内容 |
|---|---|
| 本地稿 | 路径（若保留） |
| 云文档标题 | … |
| 目录 | 我的文档 / 工程设计复盘 |
| 链接 | … |
| 一句话结论 | … |

## 安全边界

- 不改共享权限、不删云文档、不群发通知，除非用户明确要求
- 不把凭证写入文档或本仓库
- 外部写入仅限用户授权的钉钉文档创建/更新
