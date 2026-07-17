# Ethan 的 Agent Skills

这个仓库是个人 Agent Skills 的唯一源码来源，用于在 Ubuntu/Cursor、Mac/Codex 和其他兼容 Agent Skills 的环境之间同步能力。Skill 的说明与操作流程统一使用中文；目录名使用小写英文和连字符，以兼容各平台加载规则。

## 当前 Skills

| Skill | 分类 | 用途 |
|---|---|---|
| `work-module-docs` | 工作 | 分析代码模块，生成或更新设计型 `README.md` 与测试部使用的 `TEST_GUIDE.md` |
| `work-cloud-doc-publisher` | 工作 | 通过飞书或钉钉官方 CLI Skills，把本地文档可靠发布到指定云目录 |

## 仓库结构

```text
agent-skills/
├── AGENTS.md                     # Agent 维护仓库时必须遵守的规则
├── README.md                     # 使用与管理说明
├── skills/                       # 可安装的 Skill，保持一层扁平目录
│   ├── work-module-docs/
│   └── work-cloud-doc-publisher/
├── scripts/
│   ├── link_skills.py            # 把仓库 Skill 链接到不同 Agent 的用户目录
│   └── validate_repo.py          # 本地与 CI 结构检查
└── .github/workflows/
    └── validate.yml              # 提交后自动检查
```

不把飞书、钉钉或其他厂商的官方 Skills 复制进本仓库。第三方 Skill 由其官方安装器维护，本仓库只保存自己编写的编排与工作流 Skill，避免版本分叉和供应链混淆。

## 安装到 Cursor

在仓库根目录执行：

```bash
python3 scripts/link_skills.py --target cursor
```

默认把 `skills/` 下的全部 Skill 链接到 `~/.cursor/skills/`。只安装指定 Skill：

```bash
python3 scripts/link_skills.py --target cursor work-module-docs work-cloud-doc-publisher
```

预览而不写入：

```bash
python3 scripts/link_skills.py --target cursor --dry-run
```

脚本不会覆盖现有文件或指向其他位置的软链接；发生冲突时会停止并报告路径。

## 安装到其他环境

```bash
# 通用 Agent Skills 目录
python3 scripts/link_skills.py --target agents

# Codex 用户 Skills 目录
python3 scripts/link_skills.py --target codex
```

目录映射：

| 目标 | 用户目录 |
|---|---|
| `cursor` | `~/.cursor/skills/` |
| `agents` | `~/.agents/skills/` |
| `codex` | `$CODEX_HOME/skills/`；未设置时为 `~/.codex/skills/` |

项目专用 Skill 应直接放在项目自己的 `.cursor/skills/`，不要加入这个跨项目的个人仓库。

## 日常更新流程

1. 只在本仓库的 `skills/<skill-name>/` 中修改源码。
2. 执行 `python3 scripts/validate_repo.py`。
3. 新增、安装或更新 Skill 前，使用 NVIDIA SkillSpector 扫描完整 Skill 目录并完成人工行为审查。
4. 提交并推送仓库；其他机器拉取后，已有软链接会立即指向新版本。

不要在 `~/.cursor/skills/`、`~/.agents/skills/` 或 `~/.codex/skills/` 的链接目录里直接维护多份副本。

## 官方依赖

`work-cloud-doc-publisher` 只负责编排，不内置平台凭证和厂商代码：

- 飞书使用官方 [`larksuite/cli`](https://github.com/larksuite/cli) 及 `lark-shared`、`lark-doc`、`lark-drive` Skills。
- 钉钉使用官方 [DingTalk Workspace CLI](https://open.dingtalk.com/dingtalk-cli) 及其安装的文档/云盘 Skills。

所有账号授权和最小权限设置都在各平台官方 CLI 中完成，Token、Secret、Cookie 和私钥不得进入本仓库。
