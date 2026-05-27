# Programa de Reconocimiento de Voz

Una aplicación de escritorio para reconocimiento de voz con aceleración GPU ejecutada localmente para Windows. Convierte el audio hablado en texto, identifica hablantes individuales, opcionalmente traduce el resultado y entrega la salida en múltiples formatos configurables.

**Versión 1.0** — publicada el 21/05/2026

[English](README.md) | [Deutsch](README.de.md) | [Suomi](README.fi.md) | [Русский](README.ru.md) | [简体中文](README.zh_CN.md) | [繁體中文](README.zh_TW.md)

---

## Características

- Conversión de voz a texto mediante faster-whisper (aceleración CUDA; compatible con CPU como alternativa)
- Diarización de hablantes mediante pyannote.audio — hasta 10 hablantes simultáneos
- Traducción local (Helsinki-NLP OPUS-MT, sin conexión) u online (Google Translate)
- Formatos de salida: texto plano, DOCX, subtítulos SRT, JSON, portapapeles
- Procesamiento por lotes con cola FIFO
- Biblioteca de perfiles de voz: almacenar e identificar hablantes nominados entre sesiones
- Gestión de grupos de hablantes para identificación específica por contexto
- Teclas de acceso directo globales configurables (en todo el sistema, incluso minimizado)
- Modos de grabación Regular y Sesión Corta
- Modo GUI (CustomTkinter) y modo CLI completo
- Integración en la bandeja del sistema con notificaciones
- Historial de sesiones con regeneración retroactiva de salida
- Copia de seguridad y restauración de todos los datos de usuario

---

## Requisitos del Sistema

| Requisito | Detalles |
|-----------|---------|
| SO | Windows 10 u 11, 64 bits |
| GPU | GPU NVIDIA con CUDA recomendada (RTX 3060 Ti o mejor); compatible con CPU como alternativa |
| RAM | 4 GB mínimo; 8 GB recomendado para archivos de 30 minutos o más |
| Disco | 10 GB libres (incluye todos los tamaños de modelos Whisper y pares de idiomas OPUS-MT) |
| VLC | Requerido para reproducción de audio — el instalador descarga VLC automáticamente si está ausente |
| FFmpeg | Requerido para extracción de MP4/AVI — debe estar en PATH al ejecutar desde el código fuente |

---

## Inicio Rápido — Instalador

1. Descarga `wsp_setup.exe` desde la [última versión de GitHub](../../releases/latest).
2. Ejecuta el instalador y sigue el asistente:
   - Selecciona un modelo Whisper (se recomienda Medium).
   - Acepta la licencia de HuggingFace pyannote si deseas identificación de hablantes.
3. Inicia el **Programa de Reconocimiento de Voz** desde el acceso directo del escritorio o el Menú Inicio.
4. Selecciona un dispositivo de entrada o arrastra un archivo de audio a la cola por lotes y presiona **Iniciar**.

---

## Inicio Rápido — Desde el Código Fuente

```bat
git clone https://github.com/Leofaidev/SpeechRecognition.git
cd SpeechRecognition
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

> **Nota:** PyAudio requiere Microsoft C++ Build Tools y PortAudio mediante vcpkg antes de `pip install`.
> Consulta los comentarios al inicio de `requirements.txt` para instrucciones paso a paso.
> FFmpeg debe estar instalado en el sistema y en el PATH.

---

## Uso en Línea de Comandos

```bat
wsp.exe --input interview.mp3 --output-format txt json
wsp.exe --input a.mp3 b.wav --output-folder C:\Output --speaker-group "Interviewers"
wsp.exe --backup C:\Backups\wsp_backup.zip
wsp.exe --help
```

Consulta [docs/CLI.md](docs/CLI.md) para la referencia completa de parámetros y códigos de salida.

---

## Idiomas de la Interfaz

Inglés, Alemán, Español, Finés, Ruso, Chino Simplificado, Chino Tradicional.

> Las traducciones al ruso y chino son automatizadas. La revisión por hablantes nativos está pendiente.

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [docs/Specification.md](docs/Specification.md) | Especificación técnica completa (v1.0) |
| [docs/WorkPlan.md](docs/WorkPlan.md) | Plan de trabajo por fases (Fases 0–9) |
| [docs/CLI.md](docs/CLI.md) | Referencia de parámetros de línea de comandos |
| [docs/BUILD.md](docs/BUILD.md) | Instrucciones de compilación del instalador (desde el código fuente) |
| [docs/SPEAKER_JSON_SCHEMA.md](docs/SPEAKER_JSON_SCHEMA.md) | Formato `speaker.json` del perfil de voz |
| [docs/SESSION_JSON_SCHEMA.md](docs/SESSION_JSON_SCHEMA.md) | Formato JSON del historial de sesiones |
| [docs/RELEASE_NOTES_v1.0.md](docs/RELEASE_NOTES_v1.0.md) | Notas de la versión v1.0 |

---

## Bibliotecas

Todas las bibliotecas son gratuitas y de código abierto. Consulta `requirements.txt` para versiones fijas.

| Biblioteca | Función | Licencia |
|------------|---------|---------|
| faster-whisper | Conversión de voz a texto y detección de idioma | MIT |
| pyannote.audio | Diarización de hablantes (requiere licencia HuggingFace) | MIT |
| CustomTkinter | Interfaz gráfica de usuario | MIT |
| pyaudio | Captura de audio de micrófono y cámara web | MIT |
| OpenCV | Acceso al flujo de vídeo de la cámara web | Apache 2.0 |
| keyboard | Teclas de acceso directo globales | MIT |
| transformers + sentencepiece | Traducción local Helsinki-NLP OPUS-MT | Apache 2.0 |
| python-vlc | Reproducción de audio/vídeo | LGPL 2.1 |
| python-docx | Salida en formato DOCX | MIT |
| PyInstaller | Empaquetado de aplicaciones | GPL + excepción del cargador de arranque |
| Inno Setup | Instalador de Windows (herramienta separada) | Licencia de Inno Setup |
| PyTorch | Entorno de ejecución de aprendizaje profundo | BSD 3-Clause |

> **Licencia HuggingFace:** pyannote.audio requiere aceptar la licencia del modelo HuggingFace.
> Si no se acepta, la identificación de hablantes está desactivada y todos los hablantes se etiquetan como Desconocido.

---

## Contribuciones / Problemas

Este es un repositorio privado. Para reportar un error o solicitar una función, abre un issue en GitHub.
