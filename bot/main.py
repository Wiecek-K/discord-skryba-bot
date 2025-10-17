# bot/main.py
import discord
from discord import app_commands
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import config
from commands import register_commands

# --- KROK 1: Inicjalizacja usług PRZED uruchomieniem bota ---
print("LOG [Main]: Inicjalizacja klienta Qdrant...")
try:
    # --- POPRAWKA LITERÓWKI ---
    qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    qdrant_client.get_collections()
    print("LOG [Main]: Pomyślnie połączono z Qdrant.")
except Exception as e:
    print(f"KRYTYCZNY BŁĄD [Main]: Nie udało się połączyć z Qdrant. Błąd: {e}")
    qdrant_client = None

print(f"LOG [Main]: Ładowanie modelu Sentence Transformer '{config.MODEL_NAME}'... (To może potrwać kilka minut przy pierwszym uruchomieniu)")
try:
    search_model = SentenceTransformer(config.MODEL_NAME)
    print("LOG [Main]: Model został pomyślnie załadowany.")
except Exception as e:
    print(f"KRYTYCZNY BŁĄD [Main]: Nie udało się załadować modelu AI. Błąd: {e}")
    search_model = None

# --- Konfiguracja bota ---
intents = discord.Intents.default()
intents.guilds = True
bot = discord.Client(intents=intents)
# Przypisujemy zainicjalizowane usługi do obiektu bota, aby były dostępne w komendach
bot.qdrant_client = qdrant_client
bot.search_model = search_model
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    """
    Wywoływane, gdy bot pomyślnie połączy się z Discordem.
    Teraz ta funkcja jest szybka i tylko synchronizuje komendy.
    """
    print(f'LOG [Main]: Zalogowano jako {bot.user}')
    print("LOG [Main]: Synchronizowanie drzewa komend...")
    guild = discord.Object(id=config.TEST_GUILD_ID)
    await tree.sync(guild=guild)
    print(f"LOG [Main]: Zsynchronizowano komendy dla serwera deweloperskiego (ID: {config.TEST_GUILD_ID}).")

@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"LOG [Main]: Bot dołączył do serwera: {guild.name} (ID: {guild.id})")
    if not discord.utils.get(guild.roles, name=config.AUTHORIZED_ROLE_NAME):
        print(f"LOG [Main]: Tworzenie roli '{config.AUTHORIZED_ROLE_NAME}' na serwerze {guild.name}.")
        await guild.create_role(name=config.AUTHORIZED_ROLE_NAME, reason="Rola wymagana do obsługi bota")

def main():
    if not config.DISCORD_BOT_TOKEN:
        print("KRYTYCZNY BŁĄD [Main]: Brak tokenu bota Discord.")
        return
    
    if not bot.qdrant_client or not bot.search_model:
        print("KRYTYCZNY BŁĄD [Main]: Bot nie może wystartować z powodu braku połączenia z Qdrant lub braku modelu AI. Sprawdź logi powyżej.")
        return

    register_commands(tree, bot)
    print("LOG [Main]: Uruchamianie bota...")
    bot.run(config.DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()
    