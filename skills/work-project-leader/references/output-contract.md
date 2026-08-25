# project_guide 输出契约

本文件定义最小目录、写作标准、链接规范和交付检查。章节可按项目特点扩充，但必需内容不能省略。

## 1. 目录契约

```text
project_guide/
├── README.md
├── project-structure.md
├── data-flow.md
├── agent_note.md
└── <按项目需要增加的章节>.md
```

建议的附加章节：

- `overview.md`：目标、边界、术语和心智模型。
- `architecture.md`：组件、依赖、接口、并发/进程边界。
- `build-run-test.md`：静态推导的环境、命令、依赖和测试现状。
- `development-map.md`：按任务/故障定位源码入口。
- `risks-and-unknowns.md`：已验证风险、文档冲突和外部待确认项。

不要为了凑目录生成空章节。

## 2. README：阅读目录

`README.md` 必须包含：

1. 项目一句话定位和当前最重要结论。
2. 快照 commit、分支、生成日期、分析前工作区状态、范围和分析方式。
3. 按学习顺序排列的章节目录，每项说明“读完能得到什么”。
4. 单独说明 `agent_note.md` 只在用户明确提示后供 Agent 读取。
5. 证据和未验证范围。

目录顺序就是推荐学习路线。至少链接到项目结构、数据链路和 Agent Note。

## 3. 项目目录结构

`project-structure.md` 必须：

- 提供裁剪后的目录树，不罗列 vendor/build/cache/大模型内部内容。
- 对每个顶层模块或包写职责、入口、重要配置、对外接口。
- 标出生成文件、二进制、模型、数据集和外部资源的用途。
- 说明测试、部署、文档与源码的关系。
- 把文件/目录链接到仓库真实位置。

## 4. 数据链路

`data-flow.md` 至少追踪一条核心链路。对每条链路写：

- 输入/触发者。
- 解析、验证、状态和关键变换。
- 核心决策。
- 输出/副作用与消费者。
- 反馈、错误、超时或 fallback。
- 改变路径的配置。
- 每个阶段对应的源码位置。

较复杂项目优先覆盖 2–5 条；可以使用 Mermaid，但正文必须独立可读。

## 5. Agent Note

`agent_note.md` 是一次性机器上下文，不追求人类叙事。开头使用精确 frontmatter：

```yaml
---
snapshot_commit: <full commit or unavailable>
snapshot_branch: <branch or unavailable>
snapshot_worktree: clean|dirty|not-a-git-repository
generated_at: YYYY-MM-DD
scope: <repository or subsystem>
maintenance: one-shot
---
```

紧接着写醒目警告：代码变更后文件可能过期，当前代码优先。

正文应紧凑包含：

- 项目身份、技术栈、运行边界和信心边界。
- 组件/包映射与依赖方向。
- 入口、关键数据链路、状态机和数据形状。
- Topic/API/Schema/配置/命令等核心契约。
- 未来修改/排障的高价值 `path:line` 索引。
- 已验证陷阱、文档冲突和待确认项。
- 分析中没有执行或没有覆盖的内容。
- HEAD 变化后先 diff 并重新核验的指令。

不要为 Agent Note 创建自动发现规则，不承诺后续维护。

## 6. 源码链接

所有指南文件位于 `project_guide/`，链接使用相对路径：

```markdown
[入口函数](../src/main.py#L42)
[关键分支](../src/controller.cpp#L120-L156)
```

规则：

- 文件链接必须真实存在。
- 优先链接符号或具体行，不只链接目录。
- GitHub/Cursor 不能识别行锚点时，在正文补 `path/to/file:line`。
- 同一结论跨文件时给出多个证据。
- 不使用本机绝对路径、`file://` 或临时目录。
- 代码片段只摘解释所需的最小范围；可跳转链接优先。

## 7. 事实表达

每条重要陈述属于以下之一：

- **已验证**：当前代码/配置/接口直接支持。
- **文档声称**：来自已有文档，尚未运行验证。
- **推断**：由结构或命名推导，明确写“推断”。
- **待确认**：需要仓库外系统、负责人或运行证据。

不要把“文件存在”写成“功能可用”，不要把“能编译推断”写成“测试通过”，不要把 README 的“推荐”写成“生产验证”。

## 8. 最终校验

交付前检查：

- 四个必需文件都存在且非空。
- README 的阅读顺序链接到所有核心章节。
- 项目结构与数据链路均有源码链接。
- 所有本地 Markdown 链接能解析。
- Agent Note frontmatter 字段完整，含过期警告和 `maintenance: one-shot`。
- 没有 Secret、个人数据、绝对本机路径、TODO 占位或无证据结论。
- 命令明确标注“已执行/未执行”。
- 原有脏文件未被修改、暂存或提交。
- 交付报告给出分支、commit、文件、校验结果和关键未知项。
