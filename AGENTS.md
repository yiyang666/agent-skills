# Agent 维护规则

## 范围

本文件适用于整个仓库。`skills/` 是个人 Skill 的唯一源码目录。

## 结构

- 每个 Skill 直接位于 `skills/<skill-name>/`，不要增加分类层级。
- Skill 名称只使用小写字母、数字和连字符，并与目录名一致。
- 分类使用名称前缀：工作类 `work-`、学习类 `learn-`、个人类 `personal-`。
- 每个 Skill 必须包含 `SKILL.md`；仅在确有复用价值时增加 `scripts/`、`references/`、`assets/`、`agents/`。
- 不在单个 Skill 目录中创建额外的 README、安装指南、更新日志或过程文档。

## 内容

- `SKILL.md` frontmatter 只允许 `name` 和 `description`。
- `description` 同时说明能力、触发场景和排除范围。
- 面向用户和 Agent 的说明使用中文；工具名、命令、路径和标准字段保留原文。
- 用命令帮助或官方 Skill 发现会变化的接口，不凭记忆写死厂商 CLI 参数。
- 不写入 Token、Secret、Cookie、私钥、个人信息、公司内部地址或真实生产数据。
- 外部写入、覆盖、删除、共享和发消息必须有明确授权与最小权限边界。

## 依赖与第三方 Skill

- 不复制厂商官方 Skill 或第三方 Skill 到本仓库；只引用其官方来源和稳定名称。
- 新增、安装、复制或更新任何外部 Skill 前，先用 NVIDIA SkillSpector 扫描完整候选并进行人工行为审查。
- 扫描不完整、来源不明或存在未解决高风险时停止操作。

## 验证

修改后至少执行：

```bash
python3 scripts/validate_repo.py
```

包含脚本的 Skill 还必须实际运行代表性正例与失败用例。发布前再次核对变更范围，不能提交凭证、扫描缓存或临时产物。
