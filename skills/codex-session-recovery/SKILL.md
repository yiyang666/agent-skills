---
name: codex-session-recovery
description: 安全诊断并修复 Codex 本地会话历史不兼容问题，尤其是 cc-switch 或其他模型源切换后出现 `input[n].content array_above_max_length`、官方模型无法续聊、压缩失败或会话持续 systemError。用于定位对应 rollout JSONL、备份后删除第三方模型写入的非兼容隐藏推理项并验证可见历史不变；不用于恢复已删除消息、修改正常对话内容、修复账号/网络/API 配置或绕过模型权限。
---

# Codex 会话恢复

通过确定性脚本修复本地 rollout 历史。把会话文件视为敏感数据：不打印消息正文，不上传历史，不访问网络。

## 安全边界

- 从独立的恢复会话操作目标会话。不要修改当前正在运行的会话。
- 先只读检查，再向用户说明目标、根因、拟删除项数量、备份位置和重启要求。
- 写入 `~/.codex` 或 `$CODEX_HOME` 前取得明确授权与所需文件系统权限。
- 只移除可识别的第三方隐藏 `reasoning` 项；保留用户消息、可见助手回复、工具调用和工具结果。
- 每次修复都在原文件旁创建权限为 `0600` 的时间戳备份，并使用原子替换。
- 不修改 SQLite、模型配置、账号凭证或其他会话。诊断不能证明属于本 Skill 的问题时停止。

## 工作流

### 1. 定位目标会话

用户未提供 thread ID 或 rollout 路径时运行：

```sh
python3 <skill-directory>/scripts/recover_session.py find --error-text array_above_max_length
```

用错误发生时间、任务标题或用户确认消除多个候选之间的歧义。不要仅凭“最近的文件”选择目标。

### 2. 只读检查

使用 thread ID：

```sh
python3 <skill-directory>/scripts/recover_session.py inspect --thread-id <thread-id>
```

或使用明确路径：

```sh
python3 <skill-directory>/scripts/recover_session.py inspect --session-file <absolute-rollout.jsonl>
```

检查结果中的 `incompatible_reasoning`。本 Skill 识别两类已知污染：

1. `reasoning.content` 是非空数组；官方 Responses API 对历史 reasoning 输入要求该数组为空。
2. 第一次人工修复只删了 `content`，但仍残留第三方 UUID 占位式 `id` 与 `encrypted_content`；Codex 重载时可能重新构造非法字段。

### 3. 修复

只有检查命中且用户授权后才增加 `--apply`：

```sh
python3 <skill-directory>/scripts/recover_session.py repair --thread-id <thread-id> --apply
```

脚本拒绝修改 `CODEX_THREAD_ID` 指向的活动会话。不要用 `--allow-active` 绕过；该选项仅供已停止前端、人工确认没有进程持有会话时使用。

### 4. 验证与重启

再次运行 `inspect`，确认：

- `incompatible_reasoning` 为 `0`；
- 用户消息、助手消息、函数/自定义工具调用及结果计数未被修复改变；
- 修复文件与备份权限均为 `0600`。

要求用户用 `Cmd+Q` 或等价方式完全退出 Codex 后重新启动。仅关闭任务或窗口不会清除内存中的旧历史对象。

## 失败处理

- JSONL 解析失败、目标不唯一、目标为活动会话或出现未知 reasoning 结构时，不写入并报告阻断原因。
- 修复后出现不同错误时，重新从日志诊断，不扩大删除范围。
- 若同一错误在重启后仍出现，比较新错误时间与 rollout 修改时间，并检查是否选错会话；不要删除可见消息来试错。
- 需要回滚时，在 Codex 完全退出后，用报告的备份恢复原文件；恢复属于覆盖操作，必须再次取得明确授权。
