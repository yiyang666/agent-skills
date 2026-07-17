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
│   ├── scan_skill.py             # 固定版本的 SkillSpector 安全扫描门禁
│   └── validate_repo.py          # 本地与 CI 结构检查
└── .github/workflows/
    ├── security-scan.yml         # PR 中运行 SkillSpector 静态扫描
    └── validate.yml              # 提交后自动检查仓库结构
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
3. 创建功能分支并向 `main` 提交 Pull Request，不直接推送 `main`。
4. 等待“仓库结构校验”和“SkillSpector 静态安全扫描”全部通过。
5. 下载或在线查看 `skillspector-reports-*` 报告，按 PR 模板完成人工行为审查。
6. 确认扫描后的 Skill 没有再次变化，再合并 Pull Request；其他机器拉取后，已有软链接会立即指向新版本。

SkillSpector 在 GitHub 托管的 Ubuntu 环境中运行，不要求个人电脑预装 CLI。工作流通过 `uvx` 获取固定提交 `36cb67d8cc1848c6fbf739861e21b5438deb0a97`，并对 `skills/` 下每个完整目录执行静态扫描（`--no-llm`）。扫描器不可用、超时、报告损坏或发现 critical/high 风险时，检查失败并阻止合并。扫描报告保留 14 天。为避免跨 Skill 引用或共享资源遗漏风险，每个 Pull Request 都会重新扫描全部 Skill。

自动扫描不会判断所有业务意图，也不能替代人工审查。尤其要核对 Skill 的声明与实际脚本、依赖、网络目标、文件访问、凭证访问和外部写入是否一致；medium 风险和敏感能力必须明确接受后才能合并。

不要在 `~/.cursor/skills/`、`~/.agents/skills/` 或 `~/.codex/skills/` 的链接目录里直接维护多份副本。

## 官方依赖

`work-cloud-doc-publisher` 只负责编排，不内置平台凭证和厂商代码：

- 飞书使用官方 [`larksuite/cli`](https://github.com/larksuite/cli) 及 `lark-shared`、`lark-doc`、`lark-drive` Skills。
- 钉钉使用官方 [DingTalk Workspace CLI](https://open.dingtalk.com/dingtalk-cli) 及其安装的文档/云盘 Skills。

所有账号授权和最小权限设置都在各平台官方 CLI 中完成，Token、Secret、Cookie 和私钥不得进入本仓库。
