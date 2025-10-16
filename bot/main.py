import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import re
from github import Github, Auth, GithubException, GithubIntegration
import asyncio
from datetime import datetime
import traceback
import chromadb
from sentence_transformers import SentenceTransformer

# --- Konfiguracja i wczytanie zmiennych środowiskowych ---
print("LOG: Wczytywanie konfiguracji z pliku .env...")
load_dotenv()

# Klucze Discord
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Konfiguracja ChromaDB
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_COLLECTION_NAME = "baza_wiedzy"

# Klucze i ID dla aplikacji GitHub
try:
    GITHUB_APP_ID = int(os.getenv("GITHUB_APP_ID"))
    GITHUB_APP_INSTALLATION_ID = int(os.getenv("GITHUB_APP_INSTALLATION_ID"))
    
    # --- ZMIANA: Poprawne i bezpieczne wczytywanie klucza z pliku ---
    private_key_path_from_env = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")
    if not private_key_path_from_env:
        raise ValueError("Zmienna GITHUB_APP_PRIVATE_KEY_PATH nie jest ustawiona w .env")
    
    # Budujemy bezwzględną ścieżkę do pliku klucza, bazując na lokalizacji TEGO skryptu
    # To sprawia, że kod działa niezależnie od tego, skąd go uruchomimy
    script_dir = os.path.dirname(__file__)
    key_file_path = os.path.abspath(os.path.join(script_dir, '..', private_key_path_from_env))
    
    print(f"LOG: Próba odczytu klucza prywatnego z pliku: {key_file_path}")
    with open(key_file_path, 'r') as f:
        GITHUB_APP_PRIVATE_KEY = f.read()
    
    GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "Wiecek-K/discord-knowledge-base-backup")
    print("LOG: Pomyślnie wczytano konfigurację GitHub App (klucz z pliku).")
except Exception as e:
    print(f"KRYTYCZNY BŁĄD: Nie udało się wczytać konfiguracji GitHub App! Sprawdź plik .env i ścieżkę do klucza. Błąd: {e}")
    GITHUB_APP_ID = None

# Nazwa roli uprawnionej
AUTHORIZED_ROLE_NAME = "Bibliotekarz"

# --- GŁÓWNA FUNKCJA LOGIKI GITHUB (WERSJA Z PULL REQUEST) ---
async def create_github_pull_request(payload: dict, interaction: discord.Interaction):
    # ... (reszta kodu bez zmian) ...
    try:
        print(f"LOG: Rozpoczynam proces tworzenia Pull Requestu dla '{payload['proposer_name']}'...")
        print("LOG: Krok 1/7 - Uwierzytelnianie w GitHub API...")
        auth = Auth.AppAuth(GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)
        gi = GithubIntegration(auth=auth)
        owner, repo_slug = GITHUB_REPO_NAME.split('/')
        installation = gi.get_repo_installation(owner=owner, repo=repo_slug)
        g = installation.get_github_for_installation()
        repo = g.get_repo(GITHUB_REPO_NAME)
        print(f"LOG: Pomyślnie uwierzytelniono i uzyskano dostęp do repozytorium: {GITHUB_REPO_NAME}")
        print("LOG: Krok 2/7 - Generowanie nazwy nowej gałęzi...")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        proposer_sanitized = re.sub(r'[^a-zA-Z0-9-]', '', payload['proposer_name']).lower()
        new_branch_name = f"proposal/{proposer_sanitized}-{timestamp}"
        print(f"LOG: Nazwa nowej gałęzi: {new_branch_name}")
        print("LOG: Krok 3/7 - Tworzenie nowej gałęzi z 'main'...")
        source_branch = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=source_branch.commit.sha)
        print(f"LOG: Pomyślnie utworzono gałąź '{new_branch_name}'.")
        file_path = f"{payload['channel_name']}/linki.md"
        print(f"LOG: Krok 4/7 - Próba pobrania pliku '{file_path}'...")
        try:
            file_content_obj = repo.get_contents(file_path, ref="main")
            current_content = file_content_obj.decoded_content.decode('utf-8')
            file_sha = file_content_obj.sha
        except GithubException as e:
            if e.status == 404:
                print(f"LOG: Plik '{file_path}' nie istnieje. Zostanie utworzony nowy.")
                current_content = "| Link | Opis |\n|---|---|"
                file_sha = None
            else:
                raise
        print("LOG: Krok 5/7 - Przygotowywanie i zapisywanie zmian w nowej gałęzi...")
        sanitized_description = payload['description'].replace('\r\n', ' ').replace('\n', ' ').replace('|', '')
        link_title = payload['url'][:30] + ('...' if len(payload['url']) > 30 else '')
        new_row = f"| [{link_title}]({payload['url']}) | {sanitized_description} |"
        final_content = current_content.strip() + '\n' + new_row
        commit_message = f"feat: Dodaje propozycję od {payload['proposer_name']}"
        if file_sha:
            repo.update_file(file_path, commit_message, final_content, file_sha, branch=new_branch_name)
        else:
            repo.create_file(file_path, commit_message, final_content, branch=new_branch_name)
        print(f"LOG: Pomyślnie zapisano zmiany w gałęzi '{new_branch_name}'.")
        print("LOG: Krok 6/7 - Tworzenie Pull Requestu...")
        pr_title = f"Propozycja od {payload['proposer_name']}: {payload['url']}"
        pr_body = f"""
        Nowa propozycja do bazy wiedzy dodana przez **@{payload['proposer_name']}**.
        **Link:**
        `{payload['url']}`
        **Opis:**
        > {payload['description']}
        ---
        *To jest automatycznie wygenerowany Pull Request.*
        """
        pr = repo.create_pull(title=pr_title, body=pr_body, head=new_branch_name, base="main")
        print(f"LOG: Pomyślnie utworzono Pull Request #{pr.number}")
        print("LOG: Krok 7/7 - Wysyłanie potwierdzenia do użytkownika.")
        await interaction.followup.send(content=f"Gotowe! Twoja propozycja została zapisana i czeka na akceptację moderatora. Możesz ją śledzić tutaj: {pr.html_url}", ephemeral=True)
    except Exception as e:
        print(f"KRYTYCZNY BŁĄD: Wystąpił nieoczekiwany błąd podczas tworzenia Pull Requestu.")
        traceback.print_exc()
        await interaction.followup.send(content="Wystąpił krytyczny błąd! Skryba upuścił atrament i nie udało się zapisać propozycji. Skontaktuj się z administratorem.", ephemeral=True)

# --- Definicja klasy okna Modal ---
class ProposalModal(discord.ui.Modal, title='Zaproponuj nowy wpis do bazy'):
    url_input = discord.ui.TextInput(label='Link (URL)', style=discord.TextStyle.short, required=True)
    description_input = discord.ui.TextInput(label='Opis', style=discord.TextStyle.paragraph, required=True, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not GITHUB_APP_ID:
            print("LOG [DEBUG]: Akcja zatrzymana, ponieważ GITHUB_APP_ID ma wartość None. Sprawdź logi startowe bota.")
            await interaction.followup.send("Błąd konfiguracji bota. Brak danych do połączenia z GitHub.", ephemeral=True)
            return
        
        payload = {
            "url": self.url_input.value,
            "description": self.description_input.value,
            "proposer_name": interaction.user.display_name,
            "channel_name": interaction.channel.name if interaction.channel else "unknown"
        }

        asyncio.create_task(create_github_pull_request(payload, interaction))

# --- Konfiguracja bota ---
intents = discord.Intents.default()
intents.guilds = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    # ... (reszta funkcji bez zmian) ...
    print(f'Zalogowano jako {bot.user}')
    print("LOG: Inicjalizacja ChromaDB i modelu Sentence Transformer...")
    try:
        bot.chroma_client = chromadb.HttpClient(host=CHROMA_HOST.split('//')[1].split(':')[0], port=int(CHROMA_HOST.split(':')[2]))
        bot.chroma_collection = bot.chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
        print("LOG: Pomyślnie połączono z ChromaDB.")
        print("LOG: Ładowanie modelu Sentence Transformer... (może to chwilę potrwać)")
        bot.search_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
        print("LOG: Model został pomyślnie załadowany.")
    except Exception as e:
        print(f"KRYTYCZNY BŁĄD: Nie udało się zainicjalizować ChromaDB lub modelu AI: {e}")
        bot.chroma_collection = None
        bot.search_model = None
    TEST_GUILD_ID = 1348715361867923537
    guild = discord.Object(id=TEST_GUILD_ID)
    await tree.sync(guild=guild)
    print(f"Zsynchronizowano komendy dla serwera deweloperskiego (ID: {TEST_GUILD_ID}).")

# --- Reszta kodu (on_guild_join, komendy, etc.) pozostaje bez zmian ---
@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"Bot dołączył do serwera: {guild.name} (ID: {guild.id})")
    existing_role = discord.utils.get(guild.roles, name=AUTHORIZED_ROLE_NAME)
    if not existing_role:
        print(f"Rola '{AUTHORIZED_ROLE_NAME}' nie istnieje. Tworzenie nowej roli...")
        try:
            await guild.create_role(name=AUTHORIZED_ROLE_NAME, reason="Rola wymagana do obsługi bota")
            print(f"Pomyślnie utworzono rolę '{AUTHORIZED_ROLE_NAME}' na serwerze {guild.name}.")
        except discord.Forbidden:
            print(f"Błąd: Brak uprawnień do tworzenia ról na serwerze {guild.name}.")
    else:
        print(f"Rola '{AUTHORIZED_ROLE_NAME}' już istnieje na serwerze {guild.name}.")

@tree.context_menu(name="Zaproponuj do bazy wiedzy")
@app_commands.checks.has_role(AUTHORIZED_ROLE_NAME)
async def propose_to_knowledge_base(interaction: discord.Interaction, message: discord.Message):
    print(f"LOG: Użytkownik '{interaction.user.display_name}' użył komendy kontekstwowej na wiadomości.")
    content = message.content
    url_regex = r"(https?://[^\s]+)"
    match = re.search(url_regex, content)
    prefilled_url = match.group(0) if match else ""
    prefilled_description = content.replace(prefilled_url, "").strip() if match else content
    modal = ProposalModal()
    modal.url_input.default = prefilled_url
    modal.description_input.default = prefilled_description
    await interaction.response.send_modal(modal)

@propose_to_knowledge_base.error
async def on_propose_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(f"Niestety, nie posiadasz uprawnień roli **'{AUTHORIZED_ROLE_NAME}'**, aby użyć tej komendy.", ephemeral=True)
    else:
        if not interaction.response.is_done():
            await interaction.response.send_message("Wystąpił nieoczekiwany błąd.", ephemeral=True)
        print(f"BŁĄD: Nieobsłużony błąd w 'propose_to_knowledge_base': {error}")

@tree.command(name="odszukaj", description="Przeszukuje bazę wiedzy w poszukiwaniu zwojów.")
async def search_command(interaction: discord.Interaction, zapytanie: str):
    print(f"LOG: Użytkownik '{interaction.user.display_name}' wyszukuje: '{zapytanie}'")
    await interaction.response.defer(ephemeral=True)
    if not hasattr(bot, 'chroma_collection') or not bot.chroma_collection or not bot.search_model:
        await interaction.followup.send("Błąd: Baza wiedzy jest obecnie niedostępna. Skontaktuj się z administratorem.", ephemeral=True)
        return
    try:
        query_embedding = bot.search_model.encode(zapytanie).tolist()
        results = bot.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        if not results['ids'][0]:
            await interaction.followup.send(f"Nie znalazłem żadnych zwójów pasujących do Twojego zapytania: \"**{zapytanie}**\"", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"📚 Znalezione zwoje dla: '{zapytanie}'",
            color=discord.Color.blue()
        )
        for i, metadata in enumerate(results['metadatas'][0]):
            url = metadata.get('url', 'Brak URL')
            link_title = metadata.get('link_title', 'Brak Tytułu')
            original_description = metadata.get('original_description', 'Brak opisu')
            source_file = metadata.get('source_file', 'Nieznane źródło')
            embed.add_field(
                name=f"Wynik #{i+1}: {link_title}",
                value=f"**Opis:** {original_description}\n**Źródło:** `{source_file}`\n**[Otwórz link]({url})**",
                inline=False
            )
        embed.set_footer(text=f"Zapytanie od: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"BŁĄD: Wystąpił błąd podczas wyszukiwania w ChromaDB.")
        traceback.print_exc()
        await interaction.followup.send("Wystąpił błąd podczas przeszukiwania biblioteki. Spróbuj ponownie później.", ephemeral=True)

# --- Uruchomienie bota ---
if DISCORD_BOT_TOKEN:
    print("LOG: Uruchamianie bota...")
    bot.run(DISCORD_BOT_TOKEN)
else:
    print("KRYTYCZNY BŁĄD: Brak tokenu bota Discord. Ustaw DISCORD_BOT_TOKEN w pliku .env")