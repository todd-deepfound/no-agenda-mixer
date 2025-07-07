# No Agenda Show Mixer

AI-powered creative mix generator for No Agenda show episodes.

## Setup

1. Copy `.env.example` to `.env` and add your GROK API key:
   ```bash
   cp config/.env.example config/.env
   ```

2. Get your GROK API key from https://docs.x.ai/docs/overview

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python mixer.py --episode 1779
```

## Features

- Downloads episodes from op3.dev
- Fetches transcripts from noagendashow.net
- Uses GROK AI to identify funny/interesting segments
- Creates creative audio mixes
- Searches clip repository at noagenda.clipgenie.com

## Project Structure

- `audio/` - Downloaded full episodes
- `transcripts/` - Episode transcripts
- `clips/` - Extracted audio clips
- `output/` - Final mixed audio files
- `config/` - Configuration files