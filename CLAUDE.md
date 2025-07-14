# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chinese QQ bot called "量产型🍊" (Mass Production Orange) built with Python using the Graia-Ariadne framework for QQ interaction via Mirai. The bot provides various features including text correction, image processing, AI services, and entertainment functions for group chats.

## Architecture

### Core Framework
- **Main framework**: Graia-Ariadne for QQ bot functionality
- **Module management**: Graia-Saya for dynamic module loading
- **Backend**: Mirai API HTTP v2 for QQ protocol interaction
- **Entry point**: `run.py` initializes the Ariadne app and loads all modules from the `modules/` directory

### Key Components
- `config.py`: Environment-based configuration (account ID, API keys, backend URLs)
- `modules/`: Individual feature modules loaded dynamically by Saya
- `models/`: Machine learning models and training code for text correction
- `assets/`: Training datasets and text resources
- `ChatGPT/`: Embedded revChatGPT library for ChatGPT integration

### Module Structure
Each module in `modules/` follows the Graia-Saya pattern:
- Uses `@channel.use(ListenerSchema)` decorators for event handling
- Imports Ariadne components for message handling
- Implements specific bot features (text correction, image processing, etc.)

## Development Commands

### Running the Bot
```bash
python3 run.py
```

### Installing Dependencies
```bash
pip3 install -r requirements.txt
```

### Docker Development
```bash
# Build and run with hot-reload
docker build -t orenji_bot .
# The Dockerfile includes inotifywait for automatic restarts on code changes
```

### Environment Setup
Required environment variables (set in your environment):
- `ACCOUNT`: QQ bot account ID
- `BACKEND_PORT`: Mirai backend port
- `TWITTER_BEARER_KEY`: Twitter API key
- `OPENAI_API_KEY`: OpenAI API key
- `LOG_FILE_PATH`: Log file location

### Mirai Setup
Install Mirai API HTTP v2:
```bash
./mcl --update-package net.mamoe:mirai-api-http --channel stable-v2 --type plugin
```

## Key Features Implementation

### Text Correction (的地得)
- Location: `models/` directory contains BERT model for Chinese grammar correction
- Uses fine-tuned BERT model (`finetuned_bert_chinese_large_7.pt`) 
- Dataset: Custom dataset from group chat data (`assets/picked_dataset_v2.txt`)

### Image Processing
- Super resolution: Calls external service at `sr-orenji.ml:6990`
- Image storage: Custom client-server system for image collection/retrieval

### AI Integration
- ChatGPT integration via embedded `revChatGPT` library
- OpenAI API for various text processing tasks

## Development Notes

### Adding New Modules
1. Create new `.py` file in `modules/` directory
2. Follow the Saya module pattern with proper imports
3. Use Ariadne event listeners and message parsing
4. The module will be automatically loaded by `run.py`

### Configuration Management
- All configuration is environment-based via `config.py`
- Docker configuration connects to Mirai at `host.docker.internal:8850`

### Testing
- Test files are located in `test/` directory
- No specific test runner configured - use standard Python testing tools

### Model Training
- Training scripts in `models/` directory
- Configuration in `models/configs.py`
- Use existing dataset format when adding new training data