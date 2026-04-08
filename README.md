# SmartFood Tracker

家庭食材效期智能管理系统 MVP。

## 技术栈

- FastAPI
- SQLite
- SQLAlchemy
- APScheduler
- HTML / CSS / JavaScript

## 本地运行

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

启动后访问：

- `/` 看板页面
- `/docs` Swagger API 文档
- `/health` 健康检查

## 环境变量

可选配置如下：

```bash
export DATABASE_URL="sqlite:///./smartfood.db"
export REMINDER_HOUR="10"
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4.1-mini"
export NOTIFICATION_PROVIDER="generic"
export NOTIFICATION_WEBHOOK_URL="https://example.com/webhook"
export NOTIFICATION_PUSHPLUS_TOKEN="your-pushplus-token"
export NOTIFICATION_SERVERCHAN_KEY="your-serverchan-sendkey"
```

说明：

- 未设置 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` 时，语音解析自动回退到本地规则解析
- `NOTIFICATION_PROVIDER` 支持 `generic` / `pushplus` / `serverchan`
- `generic` 模式下使用 `NOTIFICATION_WEBHOOK_URL` 发送原始提醒 Webhook
- `pushplus` 模式下使用 `NOTIFICATION_PUSHPLUS_TOKEN` 发送 Push Plus 消息
- `serverchan` 模式下使用 `NOTIFICATION_SERVERCHAN_KEY` 发送 Server酱消息
- 未配置对应凭据时，系统仅记录 mock 日志

## 已实现能力

- 手动录入食材
- 语音文本录入
- 过期时间升序看板
- 状态流转：`active` / `consumed` / `discarded`
- 每日提醒调度
- 30 / 7 / 3 天提醒节点
- 语音解析失败时默认加 30 天并标记待确认

## 当前语音解析策略

当前支持两层策略：

- 优先使用外部 LLM（OpenAI 兼容 `chat/completions` 接口）
- 未配置或调用失败时自动回退到本地规则解析器

规则如下：

- 识别常见位置词，如“冷冻室”“冷藏室”“零食柜”
- 识别 `YYYY-MM-DD` 格式日期
- 未识别到明确日期时，默认使用当前日期 + 30 天
- 默认日期会将条目标记为 `needs_confirmation=true`

## 通知策略

当前通知器支持三种模式：

- `generic`：向 `NOTIFICATION_WEBHOOK_URL` 发送原始 Webhook JSON
- `pushplus`：向 Push Plus 发送适配后的消息体
- `serverchan`：向 Server酱发送适配后的消息体
- 未配置时使用 mock 日志实现

可对接：

- Push Plus
- Server 酱

## 测试

```bash
.venv/bin/pytest -v
```
