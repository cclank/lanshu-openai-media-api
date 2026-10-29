# Lanshu OpenAI Media API

**面向 Agent 的 OpenAI 文本、生图与语音转写工具，保留可追溯的用量记录。**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Runtime](https://img.shields.io/badge/runtime-standard_library-475569?style=flat-square)](../../README.md#requirements)
[![Documentation](https://img.shields.io/badge/docs-7_languages-0F766E?style=flat-square)](../../README.md#documentation)
[![License](https://img.shields.io/badge/license-MIT-16A34A?style=flat-square)](../../LICENSE)
[![岚叔 X](https://img.shields.io/badge/%E5%B2%9A%E5%8F%94-X-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/LufzzLiz)

[English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md)

一个轻量 Python CLI 和可独立分发的 skill，用于调用 OpenAI 文本生成、生图、文件转写和费用查询 API。每次成功调用都会把输出文件、请求 ID 和用量保存在一起。英文 README 为主文档。

## 功能

- 通过 Responses API 生成文本，精选四个模型，支持推理强度与输出 token 上限。
- 使用 Sunburst 或 Flare 生成图片，可控制尺寸、质量、数量和格式。
- 使用 GPT-Transcribe 转写音视频文件，支持多语言提示和术语关键词。
- 通过 Admin key 按项目、API key 和模型读取费用记录。
- API 执行结果输出 JSON，便于其他 Agent 和脚本处理。

## 精选模型

| 任务 | 模型 | 选择 |
| --- | --- | --- |
| 日常文本与编程 | `gpt-6.1-sol` | 默认文本，能力与成本均衡 |
| 复杂推理与专业任务 | `gpt-6-astra` | 优先智能水平 |
| 写作与修改 | `gpt-6.1-terra` | 快速高效 |
| 聚焦任务与批量处理 | `gpt-6-luna` | 优先速度与成本 |
| 优先图片质量 | `gpt-image-2.5-sunburst` | 默认生图 |
| 优先生成速度 | `gpt-image-2.5-flare` | 快速草稿 |
| 音视频文件转文字 | `gpt-transcribe` | 默认 ASR |

模型资料核对日期：2026-10-29。明确指定的模型会原样传入，工具不自动切换模型。

## 运行要求

Python 3.9 或更高版本，运行时仅使用标准库。curl、ffprobe 和 zsh 为可选组件。curl 优先用于 HTTP 请求，ffprobe 用于读取更多音频格式的时长，zsh 可加载已有的 ~/.zshrc 配置。

## 快速开始

以下命令在项目目录执行。发起付费调用前，先在现有本地环境中配置普通 API key。

### 生成文本

```bash
python3 scripts/openai_media.py text \
  --model gpt-6.1-sol \
  --prompt "用三句话说明 API 自动化的价值。" \
  --reasoning-effort low \
  --out output/answer.txt
```

默认使用 `gpt-6.1-sol`、`medium` 推理和 4096 输出 token 上限。复杂任务可选 `gpt-6-astra`，高效写作选 `gpt-6.1-terra`，快速批量任务选 `gpt-6-luna`。用 `python3 scripts/openai_media.py models --task text` 只查看文本模型。[官方模型说明](https://developers.openai.com/api/docs/guides/latest-model).

支持 `--prompt-file` 读取 UTF-8 提示词、`--instructions` 设置高层指令，以及 `--max-output-tokens` 控制输出上限；上限包含推理 token。Astra 和 Sol 的推理强度须为 `low` 或更高，Terra 和 Luna 也支持 `none`。请求设置 `store: false`。`--dry-run` 只预览，不读取密钥、调用接口或创建文件。

文本保存为 `.txt`，旁边的 `.metadata.json` 保留响应 ID、实际返回模型、状态、request ID 和 usage。未完成、拒绝或空文本响应仍保存产物与用量，并返回 `ok: false`、退出码 1。检查 `response_status`、`incomplete_details` 和 `refusals` 后再决定是否发起新调用；POST 不自动重试。

### 生成图片

```bash
python3 scripts/openai_media.py image \
  --prompt "一只橘猫坐在阳光下的窗台上，真实摄影，无文字" \
  --out output/cat.png
```

默认生成 1 张 1024×1024、medium 质量的 PNG。快速草稿可加 --model gpt-image-2.5-flare --quality low；精细成图可用 --quality high。还支持 --prompt-file、--size、--n 和 --output-format。--dry-run 仅预览请求。已有输出文件或 metadata 会在付费请求前触发报错。

### 音频转文字

```bash
python3 scripts/openai_media.py transcribe \
  --input /absolute/path/recording.wav \
  --languages zh \
  --keyword OpenAI \
  --out output/transcript.txt
```

重复 --languages 可提供多个预期语言。--prompt 用于录音背景，重复 --keyword 用于相关术语。empty_transcript: true 表示接口返回空文本，应如实处理。当前命令处理文件，不提供麦克风实时识别、说话人分离或词级时间戳。

### 查询费用

```bash
python3 scripts/openai_media.py costs \
  --date 2026-10-29 --timezone UTC \
  --project-id YOUR_PROJECT_ID \
  --key-name YOUR_KEY_NAME \
  --model gpt-image-2.5-sunburst \
  --out output/costs.json
```

将日期和标识替换为实际值。key 名称重名时改用 --api-key-id。费用命令读取 Admin key。

### 安装命令行入口

源码脚本可直接运行。需要独立命令时，可安装到虚拟环境。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
lanshu-openai-media-api models
```

## 凭据配置

| 变量 | 用途 |
| --- | --- |
| `OPENAI_API_KEY` | 文本生成、生图和转写 |
| `OPENAI_ADMIN_KEY` | 费用查询和 key 名称解析 |
| `OPENAI_ADMIN_API_KEY` | Admin key 的兼容别名 |

优先级为：显式 --env-file 覆盖同名变量；否则读取进程环境，再按需读取 ~/.zshrc 中已导出的变量。--no-shell-env 可关闭 shell 回退。凭据文件仅解析字面量赋值，不执行其内容。shell 启动输出会被丢弃，密钥通过私有内存管道传递。

密钥保留在现有本地环境或凭据文件中，不包含在仓库、日志和分发包里。Admin key 用于查费，与媒体调用的普通 key 分开。

## 供其他 Agent 使用

项目根目录包含完整 SKILL.md、agent 元数据和调用脚本。下面的命令生成独立 skill 文件夹、ZIP 和校验清单。把生成的文件夹放入对应 Agent 的 skills 目录；Codex 通常使用 ~/.codex/skills/。调用名为 $lanshu-openai-media-api。重复构建时可用 --force 替换此前构建产物。

```bash
python3 tools/build_skill.py --output-dir dist
```

## 输出与计费边界

生图和转写输出请求的文件，以及同名 .metadata.json。记录包含请求参数、HTTP 状态、request ID、usage、耗时、输出路径和响应元数据，不包含密钥或图片 base64。

usage 是用量。Costs API 的 amount 是按 UTC 日汇总的费用；按项目、key 和模型筛选后仍不能当作单个 request ID 的收据。非 UTC 日期可能覆盖多个 UTC 日桶，须查看 returned_daily_buckets 和 date_window_exact。没有费用记录不能推断为免费。

POST 不自动重试或更换模型；GET 最多重试一次网络错误。连接中断后，先检查已有文件和 metadata，再决定下一步。

## 开发与检查

协议测试使用本地 HTTP 服务和合成数据，不需要真实 key。CI 配置覆盖 Python 3.9、3.11 和 3.13。CLI 已做过 Sunburst 生图和 30 秒中文转写实测；各文档语言不代表都完成了识别准确率测试。

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -B tools/check_docs.py
python3 -B tools/build_skill.py --output-dir dist
```

完整参数、带日期的价格参考和官方来源见 [API 说明](../../references/api-notes.md)。修改接口行为后，请同步英文文档、各语言说明和 skill。

## 许可证

[MIT](../../LICENSE) · Copyright © 2026 Lanshu.
