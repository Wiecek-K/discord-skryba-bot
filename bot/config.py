# bot/config.py
import os
from dotenv import load_dotenv

print("LOG [Config]: Wczytywanie konfiguracji z pliku .env...")
load_dotenv(dotenv_path='../.env') # Wskazujemy ścieżkę do pliku .env w głównym katalogu

# --- Konfiguracja Discord ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
AUTHORIZED_ROLE_NAME = "Bibliotekarz"
TEST_GUILD_ID = 1348715361867923537 # ID serwera deweloperskiego

# --- Konfiguracja Qdrant ---
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")

# --- Konfiguracja Modelu AI ---
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'

# --- Konfiguracja GitHub App ---
GITHUB_APP_ID = None
GITHUB_APP_INSTALLATION_ID = None
GITHUB_APP_PRIVATE_KEY = None
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "Wiecek-K/discord-knowledge-base-backup")

try:
    GITHUB_APP_ID = int(os.getenv("GITHUB_APP_ID"))
    GITHUB_APP_INSTALLATION_ID = int(os.getenv("GITHUB_APP_INSTALLATION_ID"))
    
    private_key_path_from_env = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
    if not private_key_path_from_env:
        raise ValueError("Zmienna GITHUB_APP_PRIVATE_KEY_PATH nie jest ustawiona w .env")
    
    # Ścieżka jest teraz budowana względem głównego katalogu projektu
    key_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', private_key_path_from_env))
    
    print(f"LOG [Config]: Próba odczytu klucza prywatnego z pliku: {key_file_path}")
    with open(key_file_path, 'r') as f:
        GITHUB_APP_PRIVATE_KEY = f.read()
    
    print("LOG [Config]: Pomyślnie wczytano konfigurację GitHub App.")
except Exception as e:
    print(f"KRYTYCZNY BŁĄD [Config]: Nie udało się wczytać konfiguracji GitHub App! Błąd: {e}")

print("LOG [Config]: Konfiguracja wczytana.")