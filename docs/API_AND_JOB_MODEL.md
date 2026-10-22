# API与任务模型

> 文档状态：目标API草案，当前本地Gradio原型尚未实现  
> API前缀：`/api/v1`  
> 最近更新：2026-09-02

## 1. 设计原则

- API请求快速返回；深度转换必须作为异步任务执行。
- 所有资源按用户或租户隔离。
- 创建任务、支付回调和删除操作必须幂等。
- 业务状态以PostgreSQL为准，Redis用于队列和短期进度。
- 公共错误码稳定，内部异常和堆栈不得直接返回。
- 时间使用UTC ISO 8601，ID使用不可枚举的UUID或等价标识。

## 2. 鉴权

```http
Authorization: Bearer <access_token>
```

浏览器端推荐使用安全的HttpOnly会话Cookie或短期访问令牌。对象存储上传和下载使用短期签名URL，不向浏览器暴露永久密钥。

## 3. 上传流程

### 3.1 创建上传会话

```http
POST /api/v1/uploads
Content-Type: application/json
```

```json
{
  "filename": "dance.mp4",
  "size_bytes": 1375615,
  "content_type": "video/mp4"
}
```

响应：

```json
{
  "upload_id": "upl_01...",
  "object_key": "users/usr_01/uploads/upl_01/source",
  "upload_url": "https://storage.example/...",
  "expires_at": "2026-09-02T08:10:00Z",
  "max_size_bytes": 524288000
}
```

### 3.2 完成上传

```http
POST /api/v1/uploads/{upload_id}/complete
```

服务端必须重新检查对象大小、文件头和视频元数据，不能只相信客户端声明。

响应：

```json
{
  "upload_id": "upl_01...",
  "status": "VALIDATED",
  "video": {
    "duration_ms": 7100,
    "width": 720,
    "height": 1280,
    "fps": 29.577,
    "frame_count": 210,
    "video_codec": "h264",
    "has_audio": true
  }
}
```

## 4. 创建转换任务

```http
POST /api/v1/jobs
Idempotency-Key: <客户端生成的唯一键>
Content-Type: application/json
```

```json
{
  "upload_id": "upl_01...",
  "model": "depth-anything-v2-small",
  "output_preset": "720p",
  "invert_depth": false,
  "temporal_smoothing": true,
  "keep_audio": false,
  "split_seconds": null
}
```

响应：

```json
{
  "job_id": "job_01...",
  "status": "QUEUED",
  "queue_position": 3,
  "reserved_units": 8,
  "created_at": "2026-09-02T08:05:00Z"
}
```

规则：

- 同一用户和同一 `Idempotency-Key` 的相同请求返回原任务。
- 同一个键对应不同请求体时返回 `409 IDEMPOTENCY_CONFLICT`。
- 任务创建时预占额度，不立即结算。

## 5. 查询任务

```http
GET /api/v1/jobs/{job_id}
```

```json
{
  "job_id": "job_01...",
  "status": "RUNNING",
  "progress": {
    "percent": 46.3,
    "stage": "INFERENCE",
    "processed_frames": 108,
    "total_frames": 210,
    "message": "正在生成深度图"
  },
  "queue_position": null,
  "attempt": 1,
  "created_at": "2026-09-02T08:05:00Z",
  "started_at": "2026-09-02T08:05:08Z",
  "finished_at": null,
  "result": null,
  "error": null
}
```

成功响应中的结果：

```json
{
  "result": {
    "download_url": "https://storage.example/signed/...",
    "download_expires_at": "2026-09-02T09:00:00Z",
    "duration_ms": 7100,
    "width": 720,
    "height": 1280,
    "fps": 29.577,
    "frame_count": 210,
    "size_bytes": 1523185,
    "sha256": "..."
  }
}
```

## 6. 任务列表

```http
GET /api/v1/jobs?status=SUCCEEDED&cursor=...&limit=20
```

响应必须使用游标分页，不使用深页码偏移。默认只返回当前用户的任务。

## 7. 取消任务

```http
POST /api/v1/jobs/{job_id}/cancel
```

响应：

```json
{
  "job_id": "job_01...",
  "status": "CANCEL_REQUESTED"
}
```

- 排队任务应立即取消。
- 运行任务在批次边界检查取消标记。
- 已成功、失败或删除的任务重复取消返回当前状态，不产生副作用。

## 8. 删除任务

```http
DELETE /api/v1/jobs/{job_id}
```

删除流程：

1. 将任务标记为删除中。
2. 撤销下载链接。
3. 删除输入、输出、缩略图和工作文件。
4. 保留最小化审计记录和依法必须保存的计费流水。
5. 标记为 `DELETED`。

重复调用应保持幂等。

## 9. 进度事件

### SSE

```http
GET /api/v1/jobs/{job_id}/events
Accept: text/event-stream
```

示例：

```text
event: progress
data: {"job_id":"job_01...","status":"RUNNING","stage":"INFERENCE","percent":46.3,"processed_frames":108,"total_frames":210,"at":"2026-09-02T08:05:30Z"}
```

事件类型：

- `status_changed`
- `progress`
- `queue_position`
- `retry_scheduled`
- `completed`
- `failed`
- `cancelled`

SSE断开后，客户端使用最后事件ID恢复；无法恢复时调用任务查询接口获取事实状态。

## 10. 任务状态

| 状态 | 含义 | 终态 |
|---|---|---|
| `CREATED` | 元数据已建立 | 否 |
| `UPLOADING` | 文件上传中 | 否 |
| `VALIDATING` | 格式和权限预检 | 否 |
| `QUEUED` | 等待Worker | 否 |
| `RUNNING` | 深度推理中 | 否 |
| `ENCODING` | 编码和音频处理 | 否 |
| `UPLOADING_RESULT` | 保存结果 | 否 |
| `RETRY_WAIT` | 等待自动重试 | 否 |
| `CANCEL_REQUESTED` | 等待安全取消 | 否 |
| `SUCCEEDED` | 成功且结果已校验 | 是 |
| `REJECTED` | 输入预检不通过 | 是 |
| `FAILED` | 最终失败 | 是 |
| `CANCELLED` | 已取消 | 是 |
| `EXPIRED` | 文件已到期 | 是 |
| `DELETED` | 用户文件已删除 | 是 |

## 11. 进度阶段

| 阶段 | 建议范围 |
|---|---:|
| `VALIDATION` | 0–5% |
| `MODEL_PREPARATION` | 5–10% |
| `INFERENCE` | 10–85% |
| `ENCODING` | 85–95% |
| `RESULT_UPLOAD` | 95–99% |
| `VERIFYING` | 99–100% |

百分比只能前进，重试时显示新的 `attempt`，不能让同一尝试的百分比倒退。

## 12. 公共错误格式

```json
{
  "error": {
    "code": "VIDEO_UNSUPPORTED",
    "message": "无法读取此视频，请转换为H.264 MP4后重试",
    "request_id": "req_01...",
    "retryable": false
  }
}
```

## 13. 错误码

| HTTP | 错误码 | 是否自动重试 | 说明 |
|---:|---|---|---|
| 400 | `INVALID_REQUEST` | 否 | 请求参数不合法 |
| 400 | `VIDEO_UNSUPPORTED` | 否 | 编码或容器不支持 |
| 400 | `VIDEO_TOO_LONG` | 否 | 超过时长限制 |
| 413 | `UPLOAD_TOO_LARGE` | 否 | 文件超过限制 |
| 401 | `UNAUTHENTICATED` | 否 | 未登录或令牌失效 |
| 403 | `FORBIDDEN` | 否 | 无资源访问权限 |
| 402 | `QUOTA_INSUFFICIENT` | 否 | 可用额度不足 |
| 409 | `IDEMPOTENCY_CONFLICT` | 否 | 幂等键冲突 |
| 409 | `JOB_NOT_CANCELLABLE` | 否 | 当前状态不能取消 |
| 429 | `QUEUE_FULL` | 客户端稍后重试 | 队列超过上限 |
| 503 | `GPU_UNAVAILABLE` | 是 | 暂无可用GPU Worker |
| 500 | `GPU_OOM` | 有条件 | 降低批次后最多重试一次 |
| 504 | `PROCESSING_TIMEOUT` | 有条件 | 超过任务执行时限 |
| 500 | `OUTPUT_INVALID` | 是 | 输出校验失败 |
| 500 | `INTERNAL_ERROR` | 有条件 | 未分类内部错误 |

## 14. Worker任务载荷

队列中只放任务ID和路由信息，不放视频二进制：

```json
{
  "job_id": "job_01...",
  "attempt": 1,
  "model": "depth-anything-v2-small",
  "priority": "normal",
  "requested_gpu_class": "standard"
}
```

Worker从数据库读取完整配置，并验证任务仍处于允许执行的状态。

## 15. Worker进度更新

```json
{
  "job_id": "job_01...",
  "worker_id": "gpu-worker-03",
  "attempt": 1,
  "stage": "INFERENCE",
  "processed_frames": 108,
  "total_frames": 210,
  "percent": 46.3,
  "heartbeat_at": "2026-09-02T08:05:30Z"
}
```

Worker每1秒或每若干批次更新Redis；阶段变化、重试、成功和失败必须写数据库事件。

## 16. 额度接口摘要

```http
GET /api/v1/usage/balance
GET /api/v1/usage/ledger?cursor=...
```

额度流水类型：

- `RESERVE`
- `SETTLE`
- `RELEASE`
- `REFUND`
- `GRANT`
- `EXPIRE`

流水写入必须使用唯一幂等键，余额不能仅通过缓存维护。

## 17. 版本策略

- 破坏性修改发布新的URL版本，如 `/api/v2`。
- 非破坏性字段只能追加，客户端必须忽略未知字段。
- 错误码一旦公开不得复用为其他含义。
- OpenAPI文档由代码生成并进入CI差异检查。
