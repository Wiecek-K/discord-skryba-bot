import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv
import re
from github import Github, Auth, GithubException
import asyncio
from datetime import datetime

# --- Konfiguracja i wczytanie zmiennych środowiskowych ---
print("LOG: Wczytywanie konfiguracji z pliku .env...")
load_dotenv()

# Klucze Discord
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# Pozostawiamy webhook do wyszukiwania, bo ta logika może zostać w n8n
N8N_SEARCH_WEBHOOK_URL = os.getenv("N8N_SEARCH_WEBHOOK_URL")

# Klucze i ID dla aplikacji GitHub
try:
    GITHUB_APP_ID = int(os.getenv("GITHUB_APP_ID"))
    GITHUB_APP_INSTALLATION_ID = int(os.getenv("GITHUB_APP_INSTALLATION_ID"))
    GITHUB_APP_PRIVATE_KEY = os.getenv("GITHUB_APP_PRIVATE_KEY").replace('\\n', '\n')
    GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "Wiecek-K/discord-knowledge-base-backup")
    print("LOG: Pomyślnie wczytano konfigurację GitHub App.")
except (TypeError, ValueError) as e:
    print(f"KRYTYCZNY BŁĄD: Brak kluczowych zmiennych środowiskowych dla GitHub App! Sprawdź plik .env. Błąd: {e}")
    GITHUB_APP_ID = None

# Nazwa roli uprawnionej do dodawania propozycji
AUTHORIZED_ROLE_NAME = "Bibliotekarz"

# --- GŁÓWNA FUNKCJA LOGIKI GITHUB (WERSJA Z PULL REQUEST) ---
async def create_github_pull_request(payload: dict, interaction: discord.Interaction):
    """
    Implementuje pełny przepływ tworzenia propozycji z moderacją:
    1. Tworzy nową, unikalną gałąź z 'main'.
    2. Modyfikuje plik .md w tej nowej gałęzi.
    3. Tworzy Pull Request z nowej gałęzi do 'main'.
    4. Informuje użytkownika o wyniku, podając link do PR.
    """
    try:
        print(f"LOG: Rozpoczynam proces tworzenia Pull Requestu dla '{payload['proposer_name']}'...")
        
        # 1. Uwierzytelnianie
        print("LOG: Krok 1/7 - Uwierzytelnianie w GitHub API...")
        auth = Auth.AppAuth(GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)
        gi = Github(auth=auth)
        installation = gi.get_installation(GITHUB_APP_INSTALLATION_ID)
        g = installation.get_github_for_installation()
        repo = g.get_repo(GITHUB_REPO_NAME)
        print(f"LOG: Pomyślnie uwierzytelniono i uzyskano dostęp do repozytorium: {GITHUB_REPO_NAME}")

        # 2. Tworzenie unikalnej nazwy gałęzi
        print("LOG: Krok 2/7 - Generowanie nazwy nowej gałęzi...")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        proposer_sanitized = re.sub(r'[^a-zA-Z0-9-]', '', payload['proposer_name']).lower()
        new_branch_name = f"proposal/{proposer_sanitized}-{timestamp}"
        print(f"LOG: Nazwa nowej gałęzi: {new_branch_name}")

        # 3. Tworzenie nowej gałęzi z 'main'
        print("LOG: Krok 3/7 - Tworzenie nowej gałęzi z 'main'...")
        source_branch = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=source_branch.commit.sha)
        print(f"LOG: Pomyślnie utworzono gałąź '{new_branch_name}'.")

        # 4. Pobieranie pliku
        file_path = f"{payload['channel_name']}/linki.md"
        print(f"LOG: Krok 4/7 - Próba pobrania pliku '{file_path}'...")
        try:
            file_content_obj = repo.get_contents(file_path, ref="main") # Pobieramy z main, bo nowa gałąź ma tę samą zawartość
            current_content = file_content_obj.decoded_content.decode('utf-8')
            file_sha = file_content_obj.sha
        except GithubException as e:
            if e.status == 404:
                print(f"LOG: Plik '{file_path}' nie istnieje. Zostanie utworzony nowy.")
                current_content = "| Link | Opis |\n|---|---|"
                file_sha = None
            else:
                raise

        # 5. Przygotowanie nowej treści i zapisanie zmian w NOWEJ gałęzi
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

        # 6. Tworzenie Pull Requestu
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

        # 7. Informowanie użytkownika o sukcesie
        print("LOG: Krok 7/7 - Wysyłanie potwierdzenia do użytkownika.")
        await interaction.edit_original_response(content=f"Gotowe! Twoja propozycja została zapisana i czeka na akceptację moderatora. Możesz ją śledzić tutaj: {pr.html_url}")

    except Exception as e:
        print(f"KRYTYCZNY BŁĄD: Wystąpił nieoczekiwany błąd podczas tworzenia Pull Requestu.")
	traceback.print_exc()
        await interaction.edit_original_response(content="Wystąpił krytyczny błąd! Skryba upuścił atrament i nie udało się zapisać propozycji. Skontaktuj się z administratorem.")

# --- Definicja klasy okna Modal ---
class ProposalModal(discord.ui.Modal, title='Zaproponuj nowy wpis do bazy'):
    url_input = discord.ui.TextInput(label='Link (URL)', style=discord.TextStyle.short, required=True)
    description_input = discord.ui.TextInput(label='Opis', style=discord.TextStyle.paragraph, required=True, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        if not GITHUB_APP_ID:
            await interaction.response.send_message("Błąd konfiguracji bota. Brak danych do połączenia z GitHub. Skontaktuj się z administratorem.", ephemeral=True)
            return

        await interaction.response.send_message("Skryba przy pracy... Przygotowuję Twoją propozycję dla moderatorów.", ephemeral=True)
        
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
    print(f'Zalogowano jako {bot.user}')
    # --- ZMIANA: Synchronizacja tylko z serwerem deweloperskim dla szybkości ---
    # TODO: Przed wdrożeniem produkcyjnym, zamień to na globalne `await tree.sync()`
    TEST_GUILD_ID = 1348715361867923537
    guild = discord.Object(id=TEST_GUILD_ID)
    tree.clear_commands(guild=guild) # Opcjonalnie: czyści stare komendy przy każdym starcie
    await tree.sync(guild=guild)
    print(f"Zsynchronizowano komendy dla serwera deweloperskiego (ID: {TEST_GUILD_ID}).")

# --- Automatyczne tworzenie roli ---
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

# --- Komenda kontekstowa "Zaproponuj do bazy wiedzy" ---
@tree.context_menu(name="Zaproponuj do bazy wiedzy")
@app_commands.checks.has_role(AUTHORIZED_ROLE_NAME)
async def propose_to_knowledge_base(interaction: discord.Interaction, message: discord.Message):
    print(f"LOG: Użytkownik '{interaction.user.display_name}' użył komendy kontekstowej na wiadomości.")
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
        await interaction.response.send_message("Wystąpił nieoczekiwany błąd.", ephemeral=True)
        print(f"BŁĄD: Nieobsłużony błąd w 'propose_to_knowledge_base': {error}")

# --- Komenda "/odszukaj" (nadal używa n8n) ---
@tree.command(name="odszukaj", description="Przeszukuje bazę wiedzy w poszukiwaniu zwojów.")
async def search_command(interaction: discord.Interaction, zapytanie: str):
    print(f"LOG: Użytkownik '{interaction.user.display_name}' wyszukuje: '{zapytanie}'")
    if not N8N_SEARCH_WEBHOOK_URL:
        await interaction.response.send_message("Błąd: Webhook dla wyszukiwania nie jest skonfigurowany!", ephemeral=True)
        return
        
    await interaction.response.send_message(f"Rozpoczynam poszukiwania na hasło: '{zapytanie}'...", ephemeral=True)
    payload = {
        "query": zapytanie,
        "user_name": interaction.user.display_name,
        "channel_id": str(interaction.channel_id)
    }
    try:
        requests.post(N8N_SEARCH_WEBHOOK_URL, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"BŁĄD: Błąd podczas wysyłania do n8n (wyszukiwanie): {e}")
        await interaction.edit_original_response(content="Wystąpił błąd podczas wysyłania zapytania do skryptorium.")

# --- Uruchomienie bota ---
if DISCORD_BOT_TOKEN:
    print("LOG: Uruchamianie bota...")
    bot.run(DISCORD_BOT_TOKEN)
else:
    print("KRYTYCZNY BŁĄD: Brak tokenu bota Discord. Ustaw DISCORD_BOT_TOKEN w pliku .env")
