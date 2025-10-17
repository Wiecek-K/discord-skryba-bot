# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Discord Skryba Bot is a Polish Discord bot that serves as a knowledge base management system. The bot allows users with "Bibliotekarz" (Librarian) role to propose new entries to a knowledge base through a moderated pull request process, and search the knowledge base using semantic search powered by ChromaDB and sentence transformers.

## Architecture

The project has evolved from an n8n-centric architecture to a Python-centric architecture:

- **Discord Bot (Python)**: Central application containing all business logic
- **ChromaDB**: Vector database for semantic search functionality
- **GitHub Integration**: Uses GitHub App for creating pull requests
- **Docker Compose**: Orchestrates all services

### Key Components

- `bot/main.py`: Main bot application with Discord commands and GitHub integration
- `bot/scripts/sync_to_chroma.py`: Script to sync markdown tables to ChromaDB
- `bot/test_basic.py`: Test bot without ChromaDB dependencies
- `docker-compose.yml`: Service orchestration
- `requirements.txt`: Python dependencies

## Development Commands

### Local Development

```bash
# Setup virtual environment
cd bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run test bot (without ChromaDB)
python test_basic.py

# Run main bot locally
python main.py

# Sync knowledge base to ChromaDB
python scripts/sync_to_chroma.py
```

### Docker Development

```bash
# Build and run all services
docker compose up --build

# Run in background
docker compose up -d --build

# Stop services
docker compose down

# View logs
docker compose logs -f discord-bot
docker compose logs -f chromadb
```

### Environment Setup

Copy `.env.example` to `.env` and configure:
- `DISCORD_BOT_TOKEN`: Discord bot token
- `GITHUB_APP_ID`: GitHub App ID
- `GITHUB_APP_INSTALLATION_ID`: GitHub App installation ID
- `GITHUB_APP_PRIVATE_KEY_PATH`: Path to GitHub App private key file
- `GITHUB_REPO_NAME`: Target repository (default: Wiecek-K/discord-knowledge-base-backup)
- `CHROMA_HOST`: ChromaDB host URL

## Code Architecture

### Main Bot Flow

1. **Bot Initialization** (`bot/main.py:146-166`):
   - Connects to ChromaDB
   - Loads sentence transformer model
   - Syncs commands to development guild

2. **Proposal Workflow** (`bot/main.py:182-139`):
   - Context menu command "Zaproponuj do bazy wiedzy"
   - Opens modal dialog for URL and description
   - Creates GitHub pull request with new entry

3. **Search Functionality** (`bot/main.py:205-241`):
   - `/odszukaj` slash command
   - Uses semantic search via ChromaDB
   - Returns formatted Discord embed with results

### GitHub Integration

The bot uses GitHub App authentication (`bot/main.py:53-116`) to:
- Create new branches from main
- Update or create markdown files with new entries
- Create pull requests with proper formatting

### ChromaDB Integration

- **Collection Name**: "baza_wiedzy"
- **Model**: 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
- **Sync Script**: Parses markdown tables and creates embeddings
- **Document Format**: Combines link title and description for rich context

## Knowledge Base Format

Knowledge is stored in GitHub as markdown tables:

```markdown
| Link | Opis |
|---|---|
| [Title](URL) | Description |
```

The sync script (`bot/scripts/sync_to_chroma.py`) parses these tables and creates vector embeddings by combining link titles with descriptions.

## Deployment Notes

### Production Deployment

1. Update code on server: `git pull`
2. Configure `.env` with production values
3. Rebuild and restart: `docker compose up --build -d`
4. Test bot functionality on Discord server

### GitHub Actions Workflow

The project includes a workflow for automatic ChromaDB synchronization when knowledge base files are updated in the target repository.

## Testing

- Use `bot/test_basic.py` for testing Discord integration without ChromaDB
- Test bot permissions and role functionality
- Verify GitHub App integration with test PRs
- Validate ChromaDB search functionality with sample data

## Important Considerations

- Bot currently syncs commands to a specific test guild ID (`1348715361867923537`)
- Change `tree.sync(guild=guild)` to `await tree.sync()` for global deployment
- Bot requires "Bibliotekarz" role for proposal functionality
- GitHub App needs proper permissions for repository operations
- ChromaDB container uses port mapping 8001:8000 to avoid conflicts