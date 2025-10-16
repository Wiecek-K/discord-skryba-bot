# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Discord knowledge base management bot that enables community members to propose knowledge base entries through a moderated workflow. The system uses ChromaDB for vector search capabilities and integrates with GitHub for content management.

## Architecture

The project follows a multi-service containerized architecture with four core components:

1. **Discord Bot** (`/bot/`) - Main application handling Discord interactions
2. **ChromaDB** - Vector database for semantic search capabilities
3. **n8n Workflow Engine** - Automates GitHub integration and proposal processing
4. **GitHub Repository** - Stores the knowledge base as structured Markdown files

## Development Commands

### Docker Operations
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f discord-bot
docker-compose logs -f chromadb
docker-compose logs -f n8n
```

### Bot Development
```bash
# Install dependencies
cd bot && pip install -r requirements.txt

# Run bot locally (requires environment variables)
python bot/main.py

# Sync knowledge base to ChromaDB
python bot/scripts/sync_to_chroma.py
```

### Environment Setup
Copy `.env.example` to `.env` and configure:
- Discord bot token
- GitHub App credentials
- n8n webhook URLs
- ChromaDB connection settings

## Code Architecture

### Main Bot Application (`bot/main.py`)
- **Event Handlers**: Discord slash commands, context menus, and modals
- **GitHub Integration**: Branch creation, PR generation, and content management
- **ChromaDB Client**: Vector search operations and knowledge base queries
- **Proposition Modal**: Multi-field form for knowledge base entries

### Key Components
- **Knowledge Base Tables**: Markdown tables in `it/linki.md`, `marketing/zasoby.md`, `projekty/ciekawe_narozzia.md`
- **Vector Search**: Uses paraphrase-multilingual-mpnet-base-v2 model for multilingual embeddings
- **Role-based Access**: Requires "Bibliotekarz" Discord role for proposal submissions
- **GitHub Workflow**: Automated branch creation and PR generation via GitHub App API

### n8n Workflow (`n8n/workflows/save_workflow.json`)
- Webhook-based proposal processing
- Content preparation and markdown formatting
- Discord notification automation

## File Structure

```
bot/
├── main.py                 # Main bot application (2,400+ lines)
├── requirements.txt        # Bot-specific dependencies
├── Dockerfile              # Python container configuration
└── scripts/
    └── sync_to_chroma.py   # Knowledge base sync script

n8n/
└── workflows/
    └── save_workflow.json   # GitHub integration workflow

.github/
└── workflows/
    └── sync.yml            # ChromaDB synchronization workflow

.knowledge_manifest.yml     # File indexing configuration for ChromaDB
docker-compose.yml          # Multi-service orchestration
```

## Service Ports

- Discord Bot: No external port (uses Discord API)
- ChromaDB: http://localhost:8001
- n8n: http://localhost:5679

## Dependencies

### Key Libraries
- **discord.py**: Discord bot framework
- **chromadb**: Vector database client
- **sentence-transformers**: Multilingual text embeddings
- **PyGithub**: GitHub API integration
- **requests**: HTTP requests for n8n webhooks
- **pandas**: Markdown table parsing and processing

## Language and Localization

The bot is primarily designed for Polish language users but supports multilingual embeddings through the paraphrase-multilingual-mpnet-base-v2 model for semantic search capabilities.

## Project-Specific Implementation Details

### Knowledge Base Structure
- Knowledge is stored in GitHub repository as Markdown tables
- Format: `| [Link Title](URL) | Description |`
- Files are organized by Discord channel names: `{channel_name}/linki.md`
- Currently tracks categories: IT links, marketing resources, interesting tools

### Proposal Workflow
1. User right-clicks message → "Zaproponuj do bazy wiedzy"
2. Bot extracts URL and description, opens modal for editing
3. Requires "Bibliotekarz" role to submit proposals
4. n8n workflow creates GitHub commits to `dev` branch
5. Moderators review and merge to main via Pull Request process

### Vector Search Implementation
- ChromaDB stores embeddings for semantic search
- Description includes both URL title and full description text
- Example: `[Eleven Reader] Czytnik ebooków AI (możesz wybrać głos np Piotra Fronczewskiego)`
- Search command: `/odszukaj <zapytanie>` on Discord

### GitHub Integration
- Uses GitHub App authentication for secure repository access
- Commits directly to `dev` branch (not creating PRs initially)
- Commit format: "Zasób dodany przez {username}"
- File handling: Creates new files if they don't exist, appends to existing tables

### Development Environment
- All services containerized via Docker Compose
- ChromaDB accessible on port 8001, n8n on port 5679
- Bot requires environment variables for Discord token and webhook URLs
- Health checks configured for service dependencies