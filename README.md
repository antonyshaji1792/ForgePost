# ForgePost

**ForgePost** is an open-source, web-based video editing and social media publishing platform. It lets you edit videos, generate AI voiceovers, and schedule or instantly publish content to YouTube, Instagram, Facebook, Twitter/X, and LinkedIn — all from a single browser-based dashboard.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-brightgreen)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Screenshots](#screenshots)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the App](#running-the-app)
- [Usage Guide](#usage-guide)
  - [Video Editing Tools](#video-editing-tools)
  - [Text to Speech](#text-to-speech)
  - [Social Media Publishing](#social-media-publishing)
  - [AI-Powered Content Generation](#ai-powered-content-generation)
  - [Gallery & File Management](#gallery--file-management)
- [Configuration](#configuration)
  - [Social Media API Keys](#social-media-api-keys)
  - [LLM Providers](#llm-providers)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Video Editing
- **Merge Video + Audio** — Replace or overlay a new audio track onto any video file
- **Combine Videos** — Concatenate two video clips into a single output
- **Trim Video** — Cut a video to a custom start/end time range
- **Trim Audio** — Trim audio files (MP3, WAV, AAC) to a precise time range
- **Async Processing** — All editing jobs run in the background with real-time status polling

### Text to Speech
- Convert any text into natural-sounding voiceovers using **Microsoft Edge TTS**
- Choose from dozens of neural voices (English, Tamil, and more)
- Adjust playback speed (0.5x–2.0x)
- Download generated MP3 files directly

### Social Media Publishing
- **Multi-platform support**: YouTube, Instagram, Facebook, Twitter/X, LinkedIn
- **Instant posting** or **scheduled publishing** at a specific date/time
- Add captions, titles, and hashtags per post
- Edit or delete scheduled posts before they go live
- View full posting history with per-platform results
- Background processor checks for due posts every 10 seconds

### AI-Powered Content Generation
- Auto-generate **3 catchy title variations** from any video title
- Auto-generate **3 engaging description/caption variations** from a title or existing description
- Supports multiple LLM providers: OpenRouter, OpenAI, Groq, DeepSeek, Mistral, Together AI, and more

### User Management
- Register and login with secure password hashing (bcrypt via Werkzeug)
- Per-user isolated file storage (uploads and outputs)
- Guest mode with automatic 15-minute temp file cleanup
- Session-based authentication

### Gallery & File Management
- Browse all output files organized by category (Merge, Combine, Trim, TTS, etc.)
- Preview and download any output file
- Single or bulk file deletion
- Files sorted by newest first

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.8+, Flask |
| Video Processing | MoviePy, FFmpeg |
| Text to Speech | edge-tts (Microsoft Edge Neural TTS) |
| Authentication | Werkzeug (bcrypt password hashing), CSV-based user store |
| Social Media APIs | YouTube Data API v3, Instagram (instagrapi), Facebook Graph API, Tweepy (Twitter/X), LinkedIn API v2 |
| AI / LLM | OpenRouter, OpenAI, Groq, DeepSeek, Mistral, Together AI, and more (OpenAI-compatible API) |
| Frontend | HTML5, CSS3, JavaScript (Vanilla), Jinja2 templates |
| Job Queue | In-process threading with JSON-persisted job state |
| Scheduled Posts | JSON file-based store with background thread processor |

---

## Screenshots

> Coming soon — feel free to contribute screenshots!

---

## Getting Started

### Prerequisites

- **Python 3.8+**
- **FFmpeg** installed and available in your system PATH

#### Installing FFmpeg

**Windows (Chocolatey):**
```bash
choco install ffmpeg
```

**Windows (manual):** Download from [ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add to PATH.

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

---

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/forgepost.git
   cd forgepost
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` includes:
   ```
   flask
   moviepy
   werkzeug
   edge-tts
   ```

   For social media integrations, you may also need:
   ```bash
   pip install requests tweepy instagrapi google-api-python-client google-auth-oauthlib
   ```

---

### Running the App

```bash
python app.py
```

The app will start on `http://localhost:5000`.

- Open your browser and navigate to `http://localhost:5000`
- Register a new account on the login page
- Start editing videos and scheduling posts!

---

## Usage Guide

### Video Editing Tools

All tools are available from the main dashboard. Files are processed asynchronously and appear in your **Gallery** when complete.

#### Merge Video + Audio
1. Upload a video file (MP4, AVI, MOV, MKV)
2. Upload an audio file (MP3, WAV, AAC)
3. Click **Merge** — the original audio track is replaced with the new one
4. Download the result from the Gallery

#### Combine Videos
1. Upload two video files
2. Click **Combine** — videos are concatenated end-to-end
3. Download the result from the Gallery

#### Trim Video
1. Upload a video file
2. Enter start time and end time (in seconds)
3. Click **Trim** — a clip matching that range is extracted
4. Download the result from the Gallery

#### Trim Audio
1. Upload an audio file (MP3, WAV, AAC)
2. Enter start time and end time (in seconds)
3. Click **Trim Audio**
4. Download the result from the Gallery

---

### Text to Speech

1. Navigate to the **TTS** section on the dashboard
2. Type or paste your text
3. Choose a voice from the dropdown (e.g., `en-US-AriaNeural`, `en-GB-SoniaNeural`)
4. Set the speed (default 1.0x)
5. Click **Generate** — an MP3 voiceover is saved to your Gallery

---

### Social Media Publishing

1. Go to **Settings** and add your API credentials for each platform
2. Navigate to **Social Media** dashboard
3. Select a file from your output Gallery (or upload directly)
4. Fill in the title, caption, and hashtags
5. Choose one or more platforms (YouTube, Instagram, Facebook, Twitter/X, LinkedIn)
6. Set a **scheduled time** or leave blank for immediate publishing
7. Click **Schedule Post**

Track all posts under **Post History** — you can edit or delete pending/scheduled posts.

---

### AI-Powered Content Generation

> Requires at least one LLM provider configured in Settings.

On the Social Media post form:

- **Generate Titles** — Enter your original title and click the AI button to get 3 catchy alternatives
- **Generate Descriptions** — Enter a title or existing description and click AI to get 3 engaging rewrite variations

Configure your preferred AI provider in **Settings → LLM Providers**.

---

### Gallery & File Management

- Browse all processed files organized by type (Merge, Combine, Trim Video, Trim Audio, TTS)
- Click any file to preview or download
- Use the **Delete** button to remove individual files
- Select multiple files for **Bulk Delete**

---

## Configuration

### Social Media API Keys

Go to **Settings** in the app to enter your API credentials. Here's what you need for each platform:

| Platform | Required Credentials |
|---|---|
| **YouTube** | YouTube Data API v3 Key + Channel ID |
| **Instagram** | Instagram Username + Password (instagrapi) |
| **Facebook** | Page ID + Page Access Token |
| **Twitter / X** | API Key + API Secret + Access Token + Access Token Secret |
| **LinkedIn** | OAuth2 Access Token + Person URN (and optionally Organization URN) |

> **Security Note:** API keys are stored locally in `user_settings.json`. Never commit this file to version control. It is included in `.gitignore`.

---

### LLM Providers

ForgePost supports multiple AI providers for title and description generation. Configure any one (or more) in **Settings → LLM Providers**:

| Provider | Notes |
|---|---|
| OpenRouter | Recommended — access many models via one API key |
| OpenAI | GPT-3.5 / GPT-4 |
| Groq | Fast LLaMA / Mixtral inference |
| DeepSeek | DeepSeek Chat models |
| Mistral | Mistral AI models |
| Together AI | Open-source model hosting |
| Anthropic | Claude models |
| Google | Gemini models |
| Cohere, HuggingFace, Perplexity | Additional providers |

Mark a provider as **Active** and enter your API key and model name. The first active provider with a valid API key will be used.

---

## Project Structure

```
forgepost/
├── app.py                    # Main Flask application, routes, job management
├── auth_manager.py           # User registration & authentication (CSV-based)
├── settings_manager.py       # Per-user settings read/write (JSON)
├── social_media_manager.py   # Scheduled post processing & platform dispatching
├── merge_video_audio.py      # Video + audio merge logic (MoviePy)
├── combine_video.py          # Video concatenation logic (MoviePy)
├── trim_video.py             # Video trimming logic (MoviePy)
├── trim_audio.py             # Audio trimming logic (MoviePy)
├── text_to_speech.py         # TTS generation using edge-tts
├── youtube_manager.py        # YouTube Data API v3 upload
├── instagram_manager.py      # Instagram upload via instagrapi
├── facebook_manager.py       # Facebook Graph API upload
├── twitter_manager.py        # Twitter/X upload via Tweepy
├── linkedin_manager.py       # LinkedIn API v2 video upload
├── logger_config.py          # Centralized logging setup
├── templates/                # Jinja2 HTML templates
│   ├── index.html            # Main dashboard
│   ├── login.html            # Login / Register page
│   ├── gallery.html          # Output file gallery
│   ├── social.html           # Social media post creation
│   ├── history.html          # Post history
│   ├── edit_post.html        # Edit a scheduled post
│   ├── settings.html         # API key & settings management
│   └── logs.html             # App log viewer
├── static/                   # Static assets (CSS, JS, images)
├── uploads/                  # User-uploaded files (gitignored)
├── outputs/                  # Processed output files (gitignored)
├── requirements.txt          # Python dependencies
├── jobs.json                 # Persistent job state (gitignored)
├── scheduled_posts.json      # Scheduled post store (gitignored)
└── users.csv                 # User accounts (gitignored)
```

---

## Contributing

Contributions are very welcome! Here's how to get started:

### Ways to Contribute

- Fix bugs and open issues
- Add new video editing features (filters, subtitles, watermarks, etc.)
- Improve the UI / add a modern frontend framework
- Add new social media platform integrations (TikTok, Pinterest, Threads, etc.)
- Replace file-based storage with a proper database (SQLite / PostgreSQL)
- Add unit and integration tests
- Improve documentation

### How to Contribute

1. **Fork** this repository
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** — keep commits focused and descriptive
4. **Test your changes** locally before submitting
5. **Open a Pull Request** with a clear description of what you changed and why

### Code Style

- Follow PEP 8 for Python code
- Keep functions small and focused
- Add comments for non-obvious logic
- Don't commit sensitive files (API keys, credentials, user data)

### Reporting Issues

Please open a GitHub Issue for:
- Bug reports (include steps to reproduce)
- Feature requests
- Documentation improvements

---

## Security Notes

- Do **not** commit `users.csv`, `user_settings.json`, `jobs.json`, `scheduled_posts.json`, or any `*.pickle` / `*session*.json` files
- Add a `.gitignore` before pushing that excludes these files
- The default `app.secret_key` in `app.py` should be replaced with a strong random key in production
- For production deployment, use a proper database instead of CSV/JSON file stores

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

## Acknowledgements

- [MoviePy](https://zulko.github.io/moviepy/) — video editing
- [edge-tts](https://github.com/rany2/edge-tts) — Microsoft Edge neural TTS
- [Flask](https://flask.palletsprojects.com/) — web framework
- [FFmpeg](https://ffmpeg.org/) — underlying media processing engine
- All the social media platform API teams for their documentation
