import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv
import re

# Wczytanie dedykowanych URL-i webhooków
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
N8N_PROPOSE_WEBHOOK_URL = os.getenv("N8N_PROPOSE_WEBHOOK_URL")
N8N_SEARCH_WEBHOOK_URL = os.getenv("N8N_SEARCH_WEBHOOK_URL")

# --- ZMIANA: Zmiana nazwy roli na "Bibliotekarz" ---
AUTHORIZED_ROLE_NAME = "Bibliotekarz"

# --- Definicja klasy okna Modal (bez zmian) ---
class ProposalModal(discord.ui.Modal, title='Zaproponuj nowy wpis do bazy'):
    url_input = discord.ui.TextInput(label='Link (URL)', style=discord.TextStyle.short, required=True)
    description_input = discord.ui.TextInput(label='Opis', style=discord.TextStyle.paragraph, required=True, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Skryba przy pracy. O wyniku jego prac zostaniesz poinformowany w osobnej wiadomości.", ephemeral=True)
        
        payload = {
            "url": self.url_input.value,
            "description": self.description_input.value,
            "proposer_name": interaction.user.display_name,
            "server_id": str(interaction.guild_id),
            "channel_id": str(interaction.channel_id),
            "channel_name": interaction.channel.name if interaction.channel else "unknown"
        }

        try:
            requests.post(N8N_PROPOSE_WEBHOOK_URL, json=payload, timeout=10).raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas wysyłania do n8n (propozycja): {e}")
            await interaction.edit_original_response(content="Wystąpił błąd! Skryba upuścił atrament.")

# --- Konfiguracja bota ---
intents = discord.Intents.default()
intents.guilds = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user}')
    TEST_GUILD_ID = 1348715361867923537
    guild = discord.Object(id=TEST_GUILD_ID)
    tree.clear_commands(guild=guild)
    await tree.sync(guild=guild)
    print(f"Zsynchronizowano komendy dla serwera deweloperskiego.")

# --- Automatyczne tworzenie roli (teraz "Bibliotekarz") ---
@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"Bot dołączył do serwera: {guild.name} (ID: {guild.id})")
    existing_role = discord.utils.get(guild.roles, name=AUTHORIZED_ROLE_NAME)
    
    if not existing_role:
        print(f"Rola '{AUTHORIZED_ROLE_NAME}' nie istnieje. Tworzenie nowej roli...")
        try:
            await guild.create_role(name=AUTHORIZED_ROLE_NAME, reason=f"Rola wymagana do obsługi bota")
            print(f"Pomyślnie utworzono rolę '{AUTHORIZED_ROLE_NAME}' na serwerze {guild.name}.")
        except discord.Forbidden:
            print(f"Błąd: Brak uprawnień do tworzenia ról na serwerze {guild.name}.")
    else:
        print(f"Rola '{AUTHORIZED_ROLE_NAME}' już istnieje na serwerze {guild.name}.")

# --- Ograniczenie dostępu do roli (teraz "Bibliotekarz") ---
@tree.context_menu(name="Zaproponuj do bazy wiedzy")
@app_commands.checks.has_role(AUTHORIZED_ROLE_NAME)
async def propose_to_knowledge_base(interaction: discord.Interaction, message: discord.Message):
    content = message.content
    url_regex = r"(https?://[^\s]+)"
    match = re.search(url_regex, content)
    prefilled_url = match.group(0) if match else ""
    prefilled_description = content.replace(prefilled_url, "").strip() if match else content
    modal = ProposalModal()
    modal.url_input.default = prefilled_url
    modal.description_input.default = prefilled_description
    await interaction.response.send_modal(modal)

# Obsługa błędu, gdy użytkownik nie ma wymaganej roli
@propose_to_knowledge_base.error
async def on_propose_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(f"Niestety, nie posiadasz uprawnień roli **'{AUTHORIZED_ROLE_NAME}'**, aby użyć tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message("Wystąpił nieoczekiwany błąd.", ephemeral=True)
        print(error)

# --- Logika dla KOMENDY "/odszukaj" (bez zmian) ---
@tree.command(name="odszukaj", description="Przeszukuje bazę wiedzy w poszukiwaniu zwojów.")
async def search_command(interaction: discord.Interaction, zapytanie: str):
    if not N8N_SEARCH_WEBHOOK_URL:
        await interaction.response.send_message("Błąd: Webhook dla wyszukiwania nie jest skonfigurowany!", ephemeral=True)
        return
    await interaction.response.send_message(f"Rozpoczynam poszukiwania na hasło: '{zapytanie}'...", ephemeral=True)
    payload = {"query": zapytanie, "user_name": interaction.user.display_name, "server_id": str(interaction.guild_id), "channel_id": str(interaction.channel_id)}
    try:
        requests.post(N8N_SEARCH_WEBHOOK_URL, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Błąd podczas wysyłania do n8n (wyszukiwanie): {e}")
        await interaction.edit_original_response(content="Wystąpił błąd podczas wysyłania zapytania do skryptorium.")

# --- Uruchomienie bota (bez zmian) ---
if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
else:
    print("Błąd: Brak tokenu bota Discord. Ustaw DISCORD_BOT_TOKEN w pliku .env")
