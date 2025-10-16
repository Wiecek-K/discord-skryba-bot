#!/usr/bin/env python3
"""
Test podstawowej funkcjonalności bota bez ChromaDB
"""

import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import re

print("LOG: Wczytywanie konfiguracji z pliku .env...")
load_dotenv()

# Klucze Discord
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
AUTHORIZED_ROLE_NAME = "Bibliotekarz"

# --- Definicja klasy okna Modal ---
class TestProposalModal(discord.ui.Modal, title='Test: Zaproponuj nowy wpis do bazy'):
    url_input = discord.ui.TextInput(label='Link (URL)', style=discord.TextStyle.short, required=True)
    description_input = discord.ui.TextInput(label='Opis', style=discord.TextStyle.paragraph, required=True, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"✅ Test zakończony! Otrzymano:\nURL: {self.url_input.value}\nOpis: {self.description_input.value}", ephemeral=True)

# --- Konfiguracja bota ---
intents = discord.Intents.default()
intents.guilds = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f'✅ Bot uruchomiony pomyślnie jako {bot.user}')
    print("✅ Podstawowe importy działają")
    print("✅ Modal działa")
    print("✅ Drzewo komend działa")
    print("🚀 Bot gotowy do testów!")

@tree.context_menu(name="Test: Zaproponuj do bazy wiedzy")
@app_commands.checks.has_role(AUTHORIZED_ROLE_NAME)
async def test_propose_to_knowledge_base(interaction: discord.Interaction, message: discord.Message):
    print(f"LOG: Test komendy kontekstowej przez użytkownika '{interaction.user.display_name}'")
    content = message.content
    url_regex = r"(https?://[^\s]+)"
    match = re.search(url_regex, content)
    prefilled_url = match.group(0) if match else ""
    prefilled_description = content.replace(prefilled_url, "").strip() if match else content

    modal = TestProposalModal()
    modal.url_input.default = prefilled_url
    modal.description_input.default = prefilled_description

    await interaction.response.send_modal(modal)

@test_propose_to_knowledge_base.error
async def on_test_propose_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(f"Niestety, nie posiadasz uprawnień roli **'{AUTHORIZED_ROLE_NAME}'**.", ephemeral=True)
    else:
        await interaction.response.send_message("Wystąpił nieoczekiwany błąd.", ephemeral=True)
        print(f"BŁĄD: {error}")

@tree.command(name="test_odszukaj", description="Test komendy wyszukiwania")
async def test_search_command(interaction: discord.Interaction, zapytanie: str):
    print(f"LOG: Test wyszukiwania: '{zapytanie}' przez użytkownika '{interaction.user.display_name}'")
    embed = discord.Embed(
        title=f"🔍 Test wyszukiwania dla: '{zapytanie}'",
        description="To jest testowa odpowiedź wyszukiwania.\n\nPełna funkcjonalność ChromaDB będzie dostępna po zainstalowaniu wszystkich zależności.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Status", value="🟡 Tryb testowy - bez ChromaDB", inline=False)
    embed.add_field(name="Zapytanie", value=f"`{zapytanie}`", inline=False)
    embed.set_footer(text=f"Zapytanie od: {interaction.user.display_name}")

    await interaction.response.send_message(embed=embed)

if DISCORD_BOT_TOKEN:
    print("LOG: Uruchamianie bota w trybie testowym...")
    print("INFO: Użyj /test_odszukaj do testowania wyszukiwania")
    print("INFO: Użyj menu kontekstowego na wiadomości do testowania propozycji")
    bot.run(DISCORD_BOT_TOKEN)
else:
    print("KRYTYCZNY BŁĄD: Brak tokenu bota Discord. Ustaw DISCORD_BOT_TOKEN w pliku .env")