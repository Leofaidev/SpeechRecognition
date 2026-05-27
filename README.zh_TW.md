# 語音識別程式

一款適用於 Windows 的本地執行、GPU 加速語音識別桌面應用程式。將口語音訊轉換為文字，識別各個說話者，可選擇性地翻譯結果，並以多種可配置格式輸出。

**版本 1.0** — 發布於 2026年5月21日

[English](README.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Suomi](README.fi.md) | [Русский](README.ru.md) | [简体中文](README.zh_CN.md)

---

## 功能特性

- 透過 faster-whisper 實現語音轉文字（CUDA 加速；支援 CPU 備用方案）
- 透過 pyannote.audio 實現說話者分離 — 最多支援 10 個同時說話者
- 本地翻譯（Helsinki-NLP OPUS-MT，離線）或線上翻譯（Google 翻譯）
- 輸出格式：純文字、DOCX、SRT 字幕、JSON、剪貼簿
- 支援 FIFO 佇列的批次檔案處理
- 聲音檔案庫：跨工作階段儲存和識別命名說話者
- 說話者群組管理，用於特定情境識別
- 可配置的全域快速鍵（系統級，即使最小化也可使用）
- 一般和短工作階段錄製模式
- GUI（CustomTkinter）和完整 CLI 模式
- 系統匣整合及通知功能
- 支援事後輸出再生的工作階段歷程記錄
- 所有使用者資料的備份與還原

---

## 系統需求

| 需求 | 詳情 |
|------|------|
| 作業系統 | Windows 10 或 11，64 位元 |
| GPU | 建議使用支援 CUDA 的 NVIDIA GPU（RTX 3060 Ti 或更高）；支援 CPU 備用方案 |
| 記憶體 | 最低 4 GB；處理 30 分鐘以上檔案建議 8 GB |
| 磁碟 | 10 GB 可用空間（涵蓋所有 Whisper 模型大小和 OPUS-MT 語言對） |
| VLC | 音訊播放所需 — 安裝程式在缺少時自動下載 VLC |
| FFmpeg | MP4/AVI 提取所需 — 從原始碼執行時必須在 PATH 中 |

---

## 快速入門 — 安裝程式

1. 從 [最新 GitHub 發布版本](../../releases/latest) 下載 `wsp_setup.exe`。
2. 執行安裝程式並按精靈操作：
   - 選擇 Whisper 模型（建議 Medium）。
   - 如需說話者識別，請接受 HuggingFace pyannote 授權。
3. 從桌面捷徑或開始功能表啟動**語音識別程式**。
4. 選擇輸入裝置，或將音訊檔案拖入批次佇列，然後按**開始**。

---

## 快速入門 — 從原始碼執行

```bat
git clone https://github.com/Leofaidev/SpeechRecognition.git
cd SpeechRecognition
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

> **注意：** 在 `pip install` 之前，PyAudio 需要 Microsoft C++ Build Tools 和透過 vcpkg 安裝的 PortAudio。
> 請參閱 `requirements.txt` 開頭的注解取得詳細步驟說明。
> FFmpeg 必須在系統範圍內安裝並新增至 PATH。

---

## 命令列使用

```bat
wsp.exe --input interview.mp3 --output-format txt json
wsp.exe --input a.mp3 b.wav --output-folder C:\Output --speaker-group "Interviewers"
wsp.exe --backup C:\Backups\wsp_backup.zip
wsp.exe --help
```

完整參數參考和結束代碼請參見 [docs/CLI.md](docs/CLI.md)。

---

## 介面語言

英語、德語、西班牙語、芬蘭語、俄語、簡體中文、繁體中文。

> 俄語和中文翻譯為自動產生。母語使用者審核尚待完成。

---

## 文件

| 文件 | 說明 |
|------|------|
| [docs/Specification.md](docs/Specification.md) | 完整技術規格（v1.0） |
| [docs/WorkPlan.md](docs/WorkPlan.md) | 分階段工作計畫（第 0–9 階段） |
| [docs/CLI.md](docs/CLI.md) | 命令列參數參考 |
| [docs/BUILD.md](docs/BUILD.md) | 安裝程式建置說明（從原始碼） |
| [docs/SPEAKER_JSON_SCHEMA.md](docs/SPEAKER_JSON_SCHEMA.md) | 聲音檔案 `speaker.json` 格式 |
| [docs/SESSION_JSON_SCHEMA.md](docs/SESSION_JSON_SCHEMA.md) | 工作階段歷程 JSON 格式 |
| [docs/RELEASE_NOTES_v1.0.md](docs/RELEASE_NOTES_v1.0.md) | v1.0 發行說明 |

---

## 相依函式庫

所有函式庫均為免費開源。固定版本請參見 `requirements.txt`。

| 函式庫 | 作用 | 授權 |
|--------|------|------|
| faster-whisper | 語音轉文字和語言偵測 | MIT |
| pyannote.audio | 說話者分離（需要 HuggingFace 授權） | MIT |
| CustomTkinter | 圖形使用者介面 | MIT |
| pyaudio | 麥克風和攝影機音訊擷取 | MIT |
| OpenCV | 攝影機視訊串流存取 | Apache 2.0 |
| keyboard | 全域快速鍵 | MIT |
| transformers + sentencepiece | Helsinki-NLP OPUS-MT 本地翻譯 | Apache 2.0 |
| python-vlc | 音訊/視訊播放 | LGPL 2.1 |
| python-docx | DOCX 輸出 | MIT |
| PyInstaller | 應用程式打包 | GPL + 引導程式例外 |
| Inno Setup | Windows 安裝程式（獨立工具） | Inno Setup 授權 |
| PyTorch | 深度學習執行階段 | BSD 3-Clause |

> **HuggingFace 授權：** pyannote.audio 需要接受 HuggingFace 模型授權。
> 如未接受，說話者識別將被停用，所有說話者將被標記為未知。

---

## 貢獻 / 問題回報

這是一個私有程式碼庫。如需回報錯誤或請求功能，請在 GitHub 上提交 issue。
