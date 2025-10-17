# bot/commands.py
import discord
from discord import app_commands
import re
import traceback
# --- ZMIANA IMPORTÓW ---
import config
from discord_ui import ProposalModal

def register_commands(tree: app_commands.CommandTree, bot: discord.Client):
    """
    Rejestruje wszystkie komendy bota w drzewie komend.
    """
    print("LOG [Commands]: Rejestrowanie komend...")

    @tree.context_menu(name="Zaproponuj do bazy wiedzy")
    @app_commands.checks.has_role(config.AUTHORIZED_ROLE_NAME)
    async def propose_to_knowledge_base(interaction: discord.Interaction, message: discord.Message):
        print(f"LOG [Commands]: Użytkownik '{interaction.user.display_name}' użył komendy kontekstwowej.")
        content = message.content
        match = re.search(r"(https?://[^\s]+)", content)
        modal = ProposalModal()
        modal.url_input.default = match.group(0) if match else ""
        modal.description_input.default = content.replace(modal.url_input.default, "").strip() if match else content
        await interaction.response.send_modal(modal)

    @propose_to_knowledge_base.error
    async def on_propose_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message(f"Brak uprawnień roli **'{config.AUTHORIZED_ROLE_NAME}'**.", ephemeral=True)

    @tree.command(name="odszukaj", description="Przeszukuje bazę wiedzy.")
    async def search_command(interaction: discord.Interaction, zapytanie: str):
        print(f"LOG [Commands]: Użytkownik '{interaction.user.display_name}' wyszukuje: '{zapytanie}'")
        await interaction.response.defer(ephemeral=True)

        if not hasattr(bot, 'qdrant_client') or not bot.qdrant_client or not bot.search_model:
            await interaction.followup.send("Błąd: Baza wiedzy jest niedostępna.", ephemeral=True)
            return

        try:
            query_embedding = bot.search_model.encode(zapytanie).tolist()
            search_results = bot.qdrant_client.search(
                collection_name=config.QDRANT_COLLECTION_NAME,
                query_vector=query_embedding,
                limit=5,
                score_threshold=0.35,
                with_payload=True
            )

            if not search_results:
                await interaction.followup.send(f"Nie znaleziono wyników dla: \"**{zapytanie}**\"", ephemeral=True)
                return

            embed = discord.Embed(title=f"📚 Znalezione zwoje dla: '{zapytanie}'", color=discord.Color.blue())
            for i, result in enumerate(search_results):
                payload = result.payload
                embed.add_field(
                    name=f"Wynik #{i+1}: {payload.get('link_title', 'Brak Tytułu')} (Trafność: {result.score:.2f})",
                    value=f"**Opis:** {payload.get('original_description', 'Brak opisu')}\n**Źródło:** `{payload.get('source_file', 'Nieznane')}`\n**[Otwórz link]({payload.get('url', 'Brak URL')})**",
                    inline=False
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"BŁĄD [Commands]: Wystąpił błąd podczas wyszukiwania w Qdrant.")
            traceback.print_exc()
            await interaction.followup.send("Wystąpił błąd podczas przeszukiwania biblioteki.", ephemeral=True)
    
    print("LOG [Commands]: Komendy zarejestrowane.")