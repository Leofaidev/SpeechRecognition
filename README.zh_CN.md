# 语音识别程序

一款适用于 Windows 的本地运行、GPU 加速语音识别桌面应用程序。将口语音频转换为文本，识别各个说话者，可选择性地翻译结果，并以多种可配置格式输出。

**版本 1.0** — 发布于 2026年5月21日

[English](README.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Suomi](README.fi.md) | [Русский](README.ru.md) | [繁體中文](README.zh_TW.md)

---

## 功能特性

- 通过 faster-whisper 实现语音转文字（CUDA 加速；支持 CPU 回退）
- 通过 pyannote.audio 实现说话者分离 — 最多支持 10 个同时说话者
- 本地翻译（Helsinki-NLP OPUS-MT，离线）或在线翻译（Google 翻译）
- 输出格式：纯文本、DOCX、SRT 字幕、JSON、剪贴板
- 支持 FIFO 队列的批量文件处理
- 声音档案库：跨会话存储和识别命名说话者
- 说话者群组管理，用于特定上下文识别
- 可配置的全局快捷键（系统级，即使最小化也可使用）
- 常规和短会话录制模式
- GUI（CustomTkinter）和完整 CLI 模式
- 系统托盘集成及通知功能
- 支持事后输出再生的会话历史记录
- 所有用户数据的备份与恢复

---

## 系统要求

| 要求 | 详情 |
|------|------|
| 操作系统 | Windows 10 或 11，64 位 |
| GPU | 建议使用支持 CUDA 的 NVIDIA GPU（RTX 3060 Ti 或更高）；支持 CPU 回退 |
| 内存 | 最低 4 GB；处理 30 分钟以上文件建议 8 GB |
| 磁盘 | 10 GB 可用空间（涵盖所有 Whisper 模型大小和 OPUS-MT 语言对） |
| VLC | 音频播放所需 — 安装程序在缺失时自动下载 VLC |
| FFmpeg | MP4/AVI 提取所需 — 从源码运行时必须在 PATH 中 |

---

## 快速开始 — 安装程序

1. 从 [最新 GitHub 发布版本](../../releases/latest) 下载 `wsp_setup.exe`。
2. 运行安装程序并按向导操作：
   - 选择 Whisper 模型（推荐 Medium）。
   - 如需说话者识别，请接受 HuggingFace pyannote 许可证。
3. 从桌面快捷方式或开始菜单启动**语音识别程序**。
4. 选择输入设备，或将音频文件拖入批处理队列，然后按**开始**。

---

## 快速开始 — 从源码运行

```bat
git clone https://github.com/Leofaidev/SpeechRecognition.git
cd SpeechRecognition
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

> **注意：** 在 `pip install` 之前，PyAudio 需要 Microsoft C++ Build Tools 和通过 vcpkg 安装的 PortAudio。
> 请参阅 `requirements.txt` 开头的注释获取详细步骤说明。
> FFmpeg 必须在系统范围内安装并添加到 PATH。

---

## 命令行使用

```bat
wsp.exe --input interview.mp3 --output-format txt json
wsp.exe --input a.mp3 b.wav --output-folder C:\Output --speaker-group "Interviewers"
wsp.exe --backup C:\Backups\wsp_backup.zip
wsp.exe --help
```

完整参数参考和退出代码请参见 [docs/CLI.md](docs/CLI.md)。

---

## 界面语言

英语、德语、西班牙语、芬兰语、俄语、简体中文、繁体中文。

> 俄语和中文翻译为自动生成。母语使用者审核尚待完成。

---

## 文档

| 文档 | 说明 |
|------|------|
| [docs/Specification.md](docs/Specification.md) | 完整技术规格（v1.0） |
| [docs/WorkPlan.md](docs/WorkPlan.md) | 分阶段工作计划（第 0–9 阶段） |
| [docs/CLI.md](docs/CLI.md) | 命令行参数参考 |
| [docs/BUILD.md](docs/BUILD.md) | 安装程序构建说明（从源码） |
| [docs/SPEAKER_JSON_SCHEMA.md](docs/SPEAKER_JSON_SCHEMA.md) | 声音档案 `speaker.json` 格式 |
| [docs/SESSION_JSON_SCHEMA.md](docs/SESSION_JSON_SCHEMA.md) | 会话历史 JSON 格式 |
| [docs/RELEASE_NOTES_v1.0.md](docs/RELEASE_NOTES_v1.0.md) | v1.0 发行说明 |

---

## 依赖库

所有库均为免费开源。固定版本请参见 `requirements.txt`。

| 库 | 作用 | 许可证 |
|----|------|--------|
| faster-whisper | 语音转文字和语言检测 | MIT |
| pyannote.audio | 说话者分离（需要 HuggingFace 许可证） | MIT |
| CustomTkinter | 图形用户界面 | MIT |
| pyaudio | 麦克风和摄像头音频采集 | MIT |
| OpenCV | 摄像头视频流访问 | Apache 2.0 |
| keyboard | 全局快捷键 | MIT |
| transformers + sentencepiece | Helsinki-NLP OPUS-MT 本地翻译 | Apache 2.0 |
| python-vlc | 音频/视频播放 | LGPL 2.1 |
| python-docx | DOCX 输出 | MIT |
| PyInstaller | 应用程序打包 | GPL + 引导程序例外 |
| Inno Setup | Windows 安装程序（独立工具） | Inno Setup 许可证 |
| PyTorch | 深度学习运行时 | BSD 3-Clause |

> **HuggingFace 许可证：** pyannote.audio 需要接受 HuggingFace 模型许可证。
> 如未接受，说话者识别将被禁用，所有说话者将被标记为未知。

---

## 贡献 / 问题反馈

这是一个私有代码库。如需报告错误或请求功能，请在 GitHub 上提交 issue。
