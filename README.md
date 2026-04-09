# SmartFood Tracker

家庭食材效期智能管理系统 V1。

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
- `generic` 模式下使用 `NOTIFICATION_WEBHOOK_URL` 发送原始提醒 Webhook；如果未配置地址，系统仅记录 mock 日志
- `pushplus` 模式下使用 `NOTIFICATION_PUSHPLUS_TOKEN` 发送 Push Plus 消息
- `serverchan` 模式下使用 `NOTIFICATION_SERVERCHAN_KEY` 发送 Server酱消息

## V1 首页

当前首页已经从 MVP 录入面板升级为家庭库存总控台，包含：

- 今日概览：库存总数、待确认数、7 天内到期数、已过期数
- 风险看板：按 `已过期` / `3 天内` / `7 天内` / `安全期` 分组展示 `active` 条目
- 待确认工作区：集中处理语音解析不确定条目
- 快速录入：手动录入和语音文本录入
- 完整库存：支持搜索、状态筛选、位置筛选和排序

## 接口

- `GET /api/items/summary`：返回首页概览统计，包括总数、待确认数、已过期数、7 天内到期数和位置分布
- `GET /api/items`：返回库存列表，支持筛选、搜索和排序
- `POST /api/items/voice`：接收语音转写文本，按本地规则或 LLM 解析后创建食材
- `POST /api/items/voice/webhook`：接收第三方设备或小爱同学风格的 Webhook 文本载荷
- `PUT /api/items/{id}`：仅允许编辑 `active` 且 `needs_confirmation=true` 的待确认条目
- `POST /api/items/{id}/confirm`：确认待确认条目并清除 `needs_confirmation`

`GET /api/items` 支持的查询参数：

- `status`：按状态过滤，如 `active` / `consumed` / `discarded`
- `location`：按存放位置过滤
- `q`：按食材名称或位置做模糊搜索
- `sort`：排序方式，支持 `expiry_date_asc` / `expiry_date_desc` / `entry_date_desc`

Webhook 入口支持的常见文本字段包括：

- `text`
- `raw_text`
- `query`
- `content`
- `message`

这些字段既可以是直接字符串，也可以嵌套在对象或列表中；接口会提取第一个可用文本并复用语音录入流程。成功时返回：

```json
{ "ok": true, "item_id": 1 }
```

## 已实现能力

- 手动录入食材
- 语音文本录入
- Webhook 文本接入
- 首页概览统计
- 风险优先级看板
- 完整库存搜索、筛选和排序
- 状态流转：`active` / `consumed` / `discarded`
- 每日提醒调度
- 30 / 7 / 3 天提醒节点
- 待确认条目的编辑与确认
- 移动端自适应看板
- 语音解析失败时默认加 30 天并标记待确认

## 语音与日期解析

当前支持两层策略：

- 优先使用外部 LLM（OpenAI 兼容 `chat/completions` 接口）
- 未配置或调用失败时自动回退到本地规则解析器

规则如下：

- 识别常见位置词，如“冷冻室”“冷藏室”“零食柜”
- 在明确的过期语境中识别 `YYYY-MM-DD` 格式日期
- 在明确的过期语境中识别中文相对日期：`今天`、`明天`、`后天`、`N天后`
- 识别当前年份的月末表达：`今年10月底`、`10月底`
- 识别当前年份的月日表达：`今年10月31日`、`10月31日`
- 当文本中存在明确日期时，不再使用 30 天回退
- 未识别到明确日期时，默认使用当前日期 + 30 天
- 默认日期会将条目标记为 `needs_confirmation=true`

## 通知策略

当前通知器支持三种模式：

- `generic`：向 `NOTIFICATION_WEBHOOK_URL` 发送原始 Webhook JSON
- `pushplus`：向 Push Plus 发送适配后的消息体
- `serverchan`：向 Server酱发送适配后的消息体

配置建议：

- `NOTIFICATION_PROVIDER` 默认为 `generic`
- `generic` 适合自建 Webhook、轻量推送服务或调试环境
- `pushplus` 需要配置 `NOTIFICATION_PUSHPLUS_TOKEN`
- `serverchan` 需要配置 `NOTIFICATION_SERVERCHAN_KEY`
- 若 `generic` 未提供 `NOTIFICATION_WEBHOOK_URL`，通知器会降级为 mock 日志，不会发出网络请求

可对接：

- Push Plus
- Server 酱

## 测试

```bash
.venv/bin/pytest -v
```
