# bot/discord_ui.py
import discord
import asyncio
# --- ZMIANA IMPORTÓW ---
import config
from github_handler import create_github_pull_request

class ProposalModal(discord.ui.Modal, title='Zaproponuj nowy wpis do bazy'):
    """
    Modal (okno dialogowe) do przesyłania propozycji nowego wpisu do bazy wiedzy.
    """
    url_input = discord.ui.TextInput(label='Link (URL)', style=discord.TextStyle.short, required=True)
    description_input = discord.ui.TextInput(label='Opis', style=discord.TextStyle.paragraph, required=True, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        print("LOG [UI]: Użytkownik zatwierdził Modal propozycji.")
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not config.GITHUB_APP_ID:
            print("LOG [UI]: Akcja zatrzymana, brak konfiguracji GitHub App.")
            await interaction.followup.send("Błąd konfiguracji bota. Brak danych do połączenia z GitHub.", ephemeral=True)
            return
        
        payload = {
            "url": self.url_input.value,
            "description": self.description_input.value,
            "proposer_name": interaction.user.display_name,
            "channel_name": interaction.channel.name if interaction.channel else "unknown"
        }
        print(f"LOG [UI]: Przygotowano payload, uruchamiam zadanie w tle dla GitHub: {payload}")
        asyncio.create_task(create_github_pull_request(payload, interaction))