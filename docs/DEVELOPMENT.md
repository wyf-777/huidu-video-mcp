# 开发指南

> 适用对象：本地开发者、算法工程师、后端工程师  
> 最近更新：2026-09-02

## 1. 当前环境基线

- 操作系统：Windows
- Python：3.12
- 当前虚拟环境：`.venv`
- 当前 PyTorch：CPU版本
- 当前界面：Gradio
- 当前模型：Depth Anything V2
- FFmpeg：可选；未安装时不能保留音频和转码为H.264

不要把 `.venv`、模型缓存、用户视频、输出视频和日志提交到代码仓库。

## 2. CPU开发环境

```powershell
# 先在下载后的项目根目录打开 PowerShell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

启动：

```powershell
.\.venv\Scripts\python.exe groovin_depth_converter.py
```

验证：

```powershell
.\.venv\Scripts\python.exe -c "import torch, torchvision; print(torch.__version__); print(torch.cuda.is_available())"
```

CPU环境应输出 `False`。这不是安装失败，只表示不会使用CUDA。

## 3. GPU开发环境

GPU环境与CPU环境分开，避免破坏当前可工作的原型：

```powershell
python -m venv .venv-gpu
.\.venv-gpu\Scripts\python.exe -m pip install --upgrade pip
.\.venv-gpu\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
.\.venv-gpu\Scripts\python.exe -m pip install gradio opencv-python transformers pillow numpy
```

上述CUDA源来自2026-09-02的PyTorch官方安装页。实际部署前必须重新从官方页面生成命令，不要永久复制未经验证的版本号。

验证：

```powershell
.\.venv-gpu\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA'); print(torch.cuda.get_arch_list())"
```

验收条件：

- `torch.cuda.is_available()` 为 `True`。
- 输出正确GPU名称。
- PyTorch构建包含目标GPU计算能力。
- 完成一帧和完整短视频推理。

GTX 1060 的计算能力为6.1，已位于NVIDIA旧架构列表。它可以用来验证兼容性，但商业生产环境应采用较新的GPU。

## 4. FFmpeg

用途：

- 复制原音频。
- 输出兼容性更高的H.264/AAC。
- 执行格式预检、切片和最终校验。

安装后验证：

```powershell
ffmpeg -version
ffprobe -version
```

生产环境应固定FFmpeg版本，并将版本写入镜像和构建清单。

## 5. 当前代码结构

```text
_tools/
├─ src/depth_video_converter/
│  ├─ constants.py         稳定模型和分辨率标识
│  ├─ errors.py            安全的业务异常
│  ├─ processing.py        无框架依赖的纯图像处理
│  ├─ models.py            设备选择、模型加载与进程内缓存
│  ├─ media.py             FFmpeg和最终视频封装
│  ├─ converter.py         转换流程编排及公共数据模型
│  ├─ cli.py               命令行适配器
│  └─ ui.py                Gradio适配器
├─ tests/
│  └─ unit/                快速、无模型下载的单元测试
├─ groovin_depth_converter.py  原启动方式兼容入口
├─ docs/
├─ pyproject.toml
├─ requirements.txt
├─ requirements-dev.txt
└─ README.md
```

后续新增商业服务时，在仓库内增加`apps/api`、`apps/worker`、`migrations`和`deploy`，转换算法仍由`depth_video_converter`包唯一提供，API与Worker不得复制转换代码。

### 5.1 依赖方向

```text
Gradio / CLI / 后续API与Worker
              │
              ▼
          converter
        ┌─────┼─────┐
        ▼     ▼     ▼
     models  media  processing
```

- 适配器可以依赖核心，核心不能反向依赖Gradio、FastAPI或Celery。
- `processing.py`保持纯函数，不执行文件、网络或模型加载。
- 模型名称和分辨率标识只能在`constants.py`定义一次。
- FFmpeg命令只能通过`media.py`调用，不在UI和Worker重复拼装。
- 用户可见异常来自`errors.py`，未知异常由入口统一记录和转换。

### 5.2 控制冗余的规则

- 出现第二处相同行为时先提取公共接口，不复制粘贴分支。
- 不创建含义模糊的`utils.py`；代码放入拥有明确职责的模块。
- 一个模块只承担一个主要职责，跨层协调放在`converter.py`或应用服务中。
- 使用稳定内部标识（如`small`、`720p`），中文展示文案只保留在UI适配层。
- 依赖通过构造函数注入，测试不得为了替换依赖复制生产逻辑。
- 优先删除死代码和废弃入口，不长期维护两套实现；根脚本仅作为薄兼容入口。

## 6. 配置管理

所有环境差异通过环境变量或配置文件注入，不要写死在代码中。

建议配置：

```text
APP_ENV=development
DATABASE_URL=
REDIS_URL=
OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
MODEL_ID=depth-anything/Depth-Anything-V2-Small-hf
MODEL_REVISION=
GPU_BATCH_SIZE=4
GPU_CONCURRENCY=1
MAX_VIDEO_SECONDS=60
MAX_UPLOAD_BYTES=
INPUT_RETENTION_HOURS=24
OUTPUT_RETENTION_HOURS=72
LOG_LEVEL=INFO
```

密钥只能来自密钥管理服务或部署环境，不能写入 `.env.example` 的真实值。

## 7. 推理代码规范

- 模型必须在Worker启动阶段加载并预热。
- 推理必须同时使用 `model.eval()` 和 `torch.inference_mode()`。
- CUDA混合精度使用 `torch.autocast("cuda", dtype=torch.float16)`，上线前验证输出质量。
- 帧批次必须有上限，并支持OOM时减半重试。
- 不要在每一帧调用 `torch.cuda.empty_cache()`。
- 输出插值、归一化和时间平滑必须有单元测试。
- 模型ID和revision必须进入任务记录。
- 不能依赖Hugging Face的浮动默认分支完成可重复生产。

示意：

```python
model.eval()

with torch.inference_mode():
    with torch.autocast(
        device_type="cuda",
        dtype=torch.float16,
        enabled=device.type == "cuda",
    ):
        outputs = model(**batch_inputs)
```

## 8. 视频处理规范

- 使用 `ffprobe` 获取实际编码、时长、帧率、分辨率和音轨信息。
- 不信任扩展名和浏览器提供的MIME。
- 输出宽高必须为编码器支持的偶数。
- 保留输入帧顺序和可解释的帧数规则。
- 可变帧率输入必须明确转换策略，不能静默产生音画不同步。
- 工作目录按 `job_id` 隔离。
- 输出校验成功后才能上传并标记任务成功。

## 9. 错误处理规范

内部异常与公共错误分离：

```python
try:
    process_job(job)
except UnsupportedVideoError as exc:
    fail_job(job.id, code="VIDEO_UNSUPPORTED", public_message=str(exc))
except torch.cuda.OutOfMemoryError:
    handle_oom(job)
except Exception:
    logger.exception("unexpected job failure", extra={"job_id": job.id})
    fail_job(job.id, code="INTERNAL_ERROR", public_message="处理失败，请稍后重试")
```

不得在前端返回堆栈、服务器绝对路径、密钥或内部对象存储地址。

## 10. 依赖管理

`pyproject.toml`是项目元数据、直接依赖和工具规则的唯一来源。`requirements.txt`和`requirements-dev.txt`只提供安装入口，不重复维护版本列表。

生产构建还需要：

- 使用 `pyproject.toml` 声明直接依赖。
- 生成包含哈希的锁文件。
- CPU与不同CUDA环境使用独立锁文件或镜像。
- 记录模型revision、Python、CUDA、cuDNN和FFmpeg版本。
- 定期运行漏洞扫描，但升级必须经过回归测试。

## 11. 开发流程

仓库默认分支为`main`。不要提交`.venv`、日志、模型权重、用户视频、输出视频、密钥或本地`.env`。

1. 从`main`创建短生命周期功能分支。
2. 为行为变化补充测试。
3. 本地运行格式化、静态检查和单元测试：

```powershell
.\.venv\Scripts\python.exe -m ruff format --check src tests groovin_depth_converter.py
.\.venv\Scripts\python.exe -m ruff check src tests groovin_depth_converter.py
.\.venv\Scripts\python.exe -m pytest
```

4. 在CPU环境完成基础回归。
5. 涉及推理的变更在目标GPU完成质量和性能基准。
6. 提交PR并记录兼容性、迁移和回滚方式。
7. 合并后生成变更记录和构建产物。

## 12. 完成定义

一项功能只有在以下条件全部满足时才算完成：

- 代码通过评审。
- 单元与集成测试通过。
- 用户文档和运维文档同步更新。
- 监控指标和错误码已定义。
- 数据迁移与回滚路径明确。
- GPU性能没有未经解释的显著回退。
- 不引入未审查的模型或依赖许可证。
