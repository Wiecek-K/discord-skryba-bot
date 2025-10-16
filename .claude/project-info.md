# Project Information

Jasne. Oto kompleksowy dokument projektowy, który podsumowuje naszą dyskusję. Jest napisany w sposób, który można bezpośrednio przekazać zespołowi IT – zawiera cele, architekturę, przepływy pracy i plan działania.

---

### **Dokumentacja Projektowa: Bot Wiedzy Discord**

**Wersja:** 1.0
**Data:** 24.05.2024
**Autor:** Architekt Systemów

#### 1. Streszczenie (Executive Summary)

Projekt ma na celu stworzenie bota na platformie Discord, który usprawni proces gromadzenia i wyszukiwania wiedzy (głównie linków do artykułów i zasobów) wewnątrz firmy. Obecny problem polega na trudności w odnajdywaniu wartościowych linków udostępnianych na kanałach Discord.

Rozwiązanie opiera się na **globalnej bibliotece wiedzy** przechowywanej w publicznie czytelnym repozytorium GitHub w formacie Markdown. Bot umożliwi użytkownikom proponowanie nowych wpisów w naturalny sposób (poprzez akcję na wiadomości), a moderatorzy będą zatwierdzać je przez standardowy proces Pull Request. Wyszukiwanie będzie realizowane za pomocą **bazy wektorowej (ChromaDB)**, co pozwoli na **wyszukiwanie semantyczne** (zrozumienie znaczenia zapytania), a nie tylko po słowach kluczowych.

Całość systemu będzie hostowana na firmowym serwerze VPS, a logika biznesowa zostanie w dużej mierze zaimplementowana w platformie do automatyzacji **n8n**.

#### 2. Problem i Cele Projektu

**Problem:** Wyszukiwanie wcześniej udostępnionych, wartościowych linków na kanałach Discord jest nieprzyjazne i nieefektywne. Wiedza jest rozproszona i ginie w natłoku codziennych rozmów.

**Główne Cele:**
1.  **Centralizacja Wiedzy:** Stworzenie jednego, ustrukturyzowanego źródła prawdy (Single Source of Truth) dla firmowej bazy wiedzy w postaci repozytorium GitHub.
2.  **Wyszukiwanie Semantyczne:** Umożliwienie użytkownikom odnajdywania zasobów na podstawie znaczenia ich zapytania, a nie dokładnych słów użytych w opisie.
3.  **Moderowany Proces Kontrybucji:** Zapewnienie wysokiej jakości danych poprzez proces weryfikacji (Pull Request), w którym moderatorzy zatwierdzają każdy nowy wpis.
4.  **Naturalny Interfejs Użytkownika (UX):** Minimalizacja barier wejścia poprzez umożliwienie dodawania propozycji w sposób zintegrowany z normalnym użytkowaniem Discorda (Akcje na Wiadomości).

#### 3. Architektura Systemu

System składa się z kilku kluczowych, współpracujących ze sobą komponentów, zarządzanych za pomocą Docker Compose na serwerze VPS.

**Diagram Architektury:**
  <!-- Placeholder for a real diagram, text description below is key -->

```
+----------------+      +----------------+      +-----------------+
|                |      |                |      |                 |
|  Discord User  |----->|   Discord Bot  |----->|       n8n       |
|                |      | (Gateway)      |      | (Business Logic)|
+----------------+      +----------------+      +-------+---------+
                                                        |
                                                        | (Create PR)
                                                        v
                                                +-----------------+
                                                |  GitHub Repo    |
                                                |  (.md files)    |
                                                +-----------------+
                                                        |
                                                        | (On Merge to main)
                                                        v
                                                +-----------------+
                                                | GitHub Actions  |
                                                | (Sync Script)   |
                                                +-------+---------+
                                                        |
                                                        | (Upsert Embeddings)
                                                        v
                                                +-----------------+
                                                |    ChromaDB     |
                                                | (Vector Store)  |
                                                +-----------------+
```

**Komponenty:**
*   **Bot Discord (Gateway):** Minimalistyczna aplikacja (np. w Python/Node.js), której jedynym zadaniem jest:
    *   Rejestracja komend w Discord API (w tym kluczowej Akcji na Wiadomości).
    *   Przekazywanie interakcji użytkownika (treści wiadomości, danych o autorze) na odpowiedni webhook w n8n.
*   **n8n (Logika Biznesowa):** Serce systemu, gdzie realizowane są przepływy pracy (workflows):
    *   **Workflow "Propozycja":** Odbiera dane od bota, komunikuje się z API GitHuba w celu utworzenia gałęzi i Pull Requestu.
    *   **Workflow "Wyszukiwanie":** Odbiera zapytanie od użytkownika, generuje dla niego wektor i odpytuje ChromaDB o podobne wpisy.
*   **Repozytorium GitHub (Źródło Prawdy):**
    *   Przechowuje całą bazę wiedzy w plikach `.md` (jeden plik per kategoria/kanał).
    *   Struktura danych w plikach to tabela Markdown.
    *   Proces Pull Request służy jako mechanizm moderacji i kontroli jakości.
*   **GitHub Actions (Synchronizacja):**
    *   Automatyczny proces uruchamiany po każdym zmergowaniu PR do gałęzi `main`.
    *   Uruchamia skrypt (Python), który parsuje pliki `.md`, generuje wektory (embeddingi) dla każdego wpisu i aktualizuje bazę ChromaDB.
*   **ChromaDB (Silnik Wyszukiwania):**
    *   Baza wektorowa przechowująca embeddingi opisów oraz metadane (link, pełny opis, źródło).
    *   Odpowiada za szybkie i wydajne wyszukiwanie semantyczne.

#### 4. Przepływy Pracy (Workflows)

**A. Propozycja Nowego Wpisu**
1.  **Użytkownik** znajduje interesującą wiadomość na Discordzie.
2.  Klika na nią prawym przyciskiem myszy, wybiera `Aplikacje -> "Zaproponuj do bazy wiedzy"`.
3.  **Bot Discord** przechwytuje całą treść wiadomości i wysyła ją na webhook n8n.
4.  **n8n** uruchamia workflow, który:
    a. Natychmiast odpowiada użytkownikowi, że propozycja została przyjęta.
    b. Tworzy nową gałąź w repozytorium GitHub.
    c. Dodaje nowy wiersz do tabeli w odpowiednim pliku `.md`.
    d. Tworzy Pull Request do gałęzi `main`.
    e. (Opcjonalnie) Wysyła powiadomienie z linkiem do PR na kanał dla moderatorów.

**B. Moderacja i Synchronizacja Danych**
1.  **Moderator** otrzymuje powiadomienie o nowym PR.
2.  Przegląda zmianę na GitHubie, może ją edytować lub zatwierdzić.
3.  Po zatwierdzeniu, **merguje Pull Request** do gałęzi `main`.
4.  Zmergowanie PR automatycznie uruchamia **GitHub Actions**.
5.  Skrypt w GitHub Actions:
    a. Parsuje zaktualizowane pliki `.md`.
    b. Dla każdego wpisu generuje wektor (embedding) na podstawie opisu.
    c. Wysyła dane (wektory, metadane, ID) do ChromaDB, używając operacji `upsert` (aktualizuj lub wstaw), co zapewnia spójność danych.

**C. Wyszukiwanie Wiedzy**
1.  **Użytkownik** na dowolnym kanale wpisuje komendę `/odszukaj <zapytanie>`.
2.  **Bot Discord** przekazuje zapytanie do n8n.
3.  **n8n** uruchamia workflow, który:
    a. Generuje wektor dla zapytania użytkownika.
    b. Odpytuje ChromaDB o 5 najbardziej podobnych wektorów.
    c. Otrzymuje z ChromaDB metadane powiązane z wynikami (linki, opisy).
    d. Formatuje wyniki w czytelną wiadomość i wysyła ją jako odpowiedź na Discordzie.

#### 5. Stos Technologiczny i Infrastruktura

*   **Infrastruktura:** Serwer VPS (Linux)
*   **Konteneryzacja:** Docker & Docker Compose
*   **Komponenty w Dockerze:**
    1.  `discord-bot` (Aplikacja w Python/discord.py lub Node.js/discord.js)
    2.  `n8n` (Oficjalny obraz Docker)
    3.  `chromadb` (Oficjalny obraz Docker)
*   **Automatyzacja CI/CD:** GitHub Actions
*   **Przetwarzanie Języka:** Python ze bibliotekami `sentence-transformers` i `pandas` (w ramach GitHub Actions).

#### 6. Monitoring

Proponuje się wdrożenie prostego, ale skutecznego monitoringu:
*   **Uptime Kuma:** (jako dodatkowy kontener Docker) do monitorowania dostępności usług (endpoint n8n, port ChromaDB, ping serwera).
*   **Logi Docker:** Standardowe `docker logs` jako podstawowe narzędzie do diagnostyki problemów.

#### 7. Plan Działania (Next Steps)

1.  **Faza 1: Przygotowanie Infrastruktury**
    *   Konfiguracja serwera VPS.
    *   Instalacja Dockera i Docker Compose.
    *   Utworzenie pliku `docker-compose.yml` i uruchomienie kontenerów n8n oraz ChromaDB.
2.  **Faza 2: Implementacja Bota i n8n**
    *   Stworzenie szkieletu bota Discord, który rejestruje komendy i przekazuje dane do n8n.
    *   Zbudowanie workflowów w n8n do tworzenia PR i obsługi wyszukiwania.
3.  **Faza 3: Automatyzacja Synchronizacji**
    *   Przygotowanie repozytorium GitHub z przykładową strukturą plików `.md`.
    *   Napisanie skryptu w Pythonie do parsowania, generowania embeddingów i komunikacji z ChromaDB.
    *   Skonfigurowanie workflow GitHub Actions.
4.  **Faza 4: Testowanie i Wdrożenie**
    *   Testy End-to-End całego przepływu.
    *   Instalacja bota na docelowym serwerze Discord.
    *   Przeszkolenie moderatorów i użytkowników.

-----

Raport z wczorja:

### Podsumowanie Dnia / Osiągnięcia

Dzisiaj zbudowaliśmy solidny fundament pod cały projekt. Od zera skonfigurowaliśmy całe środowisko, wdrożyliśmy aplikację i rozwiązaliśmy szereg kluczowych problemów technicznych, przygotowując grunt pod zaawansowane funkcje.

**Kluczowe zrealizowane zadania:**

1.  **Konfiguracja Serwera:** Pomyślnie zainstalowaliśmy i skonfigurowaliśmy Docker oraz Docker Compose na serwerze VPS z Debianem, radząc sobie z problemami kompatybilności powłoki `fish`.
2.  **Wdrożenie Aplikacji:** Uruchomiliśmy całą architekturę (Bot, n8n, ChromaDB) za pomocą pliku `docker-compose.yml`.
3.  **Debugging i Stabilizacja:** Zdiagnozowaliśmy i naprawiliśmy kilka problemów "wieku dziecięcego":
    *   Problem z bezpiecznymi ciasteczkami w n8n.
    *   Pętle restartów kontenera bota spowodowane błędami w składni `.env` oraz nieaktualną składnią `discord.py`.
4.  **Rozbudowa Funkcjonalności Bota:** Znacząco ulepszyliśmy interakcję z botem, implementując:
    *   **Okna Dialogowe (Modals):** Interaktywny formularz do edycji propozycji przez użytkownika.
    *   **System Ról:** Ograniczyliśmy dostęp do komendy tylko dla użytkowników z rolą "Bibliotekarz".
    *   **Automatyzację:** Bot sam tworzy wymaganą rolę po dołączeniu do nowego serwera.
5.  **Wersjonowanie Kodu (Git & GitHub):**
    *   Zainicjowaliśmy repozytorium Git i stworzyliśmy `.gitignore` do ochrony poufnych danych.
    *   Pomyślnie skonfigurowaliśmy uwierzytelnianie z GitHubem za pomocą dedykowanego klucza SSH, rozwiązując złożone problemy z uprawnieniami (Deploy Key vs Personal Key).
    *   **Cały kod projektu jest teraz bezpiecznie przechowywany na GitHubie.**

---

### Pliki do Kontynuacji Pracy (Stan na Koniec Dnia)

Oto kompletne wersje kluczowych plików, które zdefiniują nasz punkt startowy na jutro.

#### 1. Plik `docker-compose.yml`
```yaml
services:
  n8n:
    image: n8nio/n8n
    restart: always
    ports:
      - "5679:5678"
    environment:
      - TZ=Europe/Warsaw
      - N8N_SECURE_COOKIE=false
    volumes:
      - n8n_data:/home/node/.n8n
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5678/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  chromadb:
    image: chromadb/chroma
    restart: always
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/.chroma/index

  discord-bot:
    build: ./bot
    restart: always
    env_file:
      - .env
    depends_on:
      n8n:
        condition: service_healthy

volumes:
  n8n_data:
  chroma_data:
```

#### 2. Plik `bot/main.py`
*Kompletny, działający kod bota z obsługą Modali, ról i dedykowanych webhooków.*
```python
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

# Nazwa roli, która będzie uprawniona do dodawania propozycji
AUTHORIZED_ROLE_NAME = "Bibliotekarz"

# Definicja klasy okna Modal
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

# Konfiguracja bota
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

@propose_to_knowledge_base.error
async def on_propose_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(f"Niestety, nie posiadasz uprawnień roli **'{AUTHORIZED_ROLE_NAME}'**, aby użyć tej komendy.", ephemeral=True)
    else:
        await interaction.response.send_message("Wystąpił nieoczekiwany błąd.", ephemeral=True)
        print(error)

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

if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
else:
    print("Błąd: Brak tokenu bota Discord. Ustaw DISCORD_BOT_TOKEN w pliku .env")
```

#### 3. Uproszczony Workflow n8n (JSON)
*Docelowy workflow do tworzenia commitów w gałęzi `dev`.*
```json
{
  "nodes": [
    {
      "parameters": {
        "resource": "file",
        "operation": "get",
        "owner": {
          "__rl": true,
          "value": "Wiecek-K",
          "mode": "list",
          "cachedResultName": "Wiecek-K",
          "cachedResultUrl": "https://github.com/Wiecek-K"
        },
        "repository": {
          "__rl": true,
          "value": "discord-knowledge-base-backup",
          "mode": "list",
          "cachedResultName": "discord-knowledge-base-backup",
          "cachedResultUrl": "https://github.com/Wiecek-K/discord-knowledge-base-backup"
        },
        "filePath": "={{ $json.body.channel_name }}/linki.md",
        "asBinaryProperty": false,
        "additionalParameters": {
          "reference": "dev"
        }
      },
      "id": "edb4cd2f-88e7-4160-ac43-311e3c9b0b03",
      "name": "1. Pobierz plik .md z gałęzi 'dev'",
      "type": "n8n-nodes-base.github",
      "typeVersion": 1.1,
      "position": [
        -1360,
        -432
      ],
      "webhookId": "f61ff381-bb8b-4378-952e-dca4e5c362bb",
      "alwaysOutputData": false,
      "credentials": {
        "githubApi": {
          "id": "9Jm1ye1aJP8vV0bT",
          "name": "GitHub account"
        }
      },
      "onError": "continueRegularOutput"
    },
    {
      "parameters": {
        "jsCode": "// Pobieramy dane z poprzednich kroków\n// Używamy .first() na wypadek, gdyby n8n zwrócił pusty item, co zapobiega błędom\nconst fileNodeResult = $input.first();\nconst proposalData = $('WebHook: Save').first().json.body\n\nlet currentContent = '';\nlet fileSha = null;\n\n// Sprawdzamy, czy plik istnieje. Węzeł GitHub nie zwraca błędu,\n// ale może zwrócić pusty wynik, jeśli plik nie zostanie znaleziony.\n// WAŻNE: W opcjach węzła \"1. Pobierz plik...\" ustaw \"Continue on Fail\" na true.\nif (fileNodeResult && fileNodeResult.json.content) {\n  // Plik istnieje, dekodujemy jego zawartość\n  currentContent = Buffer.from(fileNodeResult.json.content, 'base64').toString('utf8');\n  fileSha = fileNodeResult.json.sha;\n} else {\n  // Plik nie istnieje lub jest pusty, tworzymy nagłówek tabeli od zera.\n  currentContent = `| Link | Opis |\\n|---|---|`;\n}\n\n// --- Przygotowanie i czyszczenie danych do wstawienia ---\n\n// 1. Czyścimy opis: usuwamy znaki nowej linii i \"|\" które mogłyby zepsuć tabelę.\nconst sanitizedDescription = proposalData.description.replace(/\\r?\\n|\\r/g, ' ').replace(/\\|/g, ' ');\n\n// 2. Tworzymy zwięzły tytuł dla linku z opisu (np. pierwsze 80 znaków)\nlet linkTitle = `${proposalData.url}`.slice(0, 30);\nif (sanitizedDescription.length > 30) {\n  linkTitle += '...';\n}\n\n// 3. Tworzymy nowy, sformatowany wiersz tabeli Markdown\nconst newRow = `| [${linkTitle}](${proposalData.url}) | ${sanitizedDescription} |`;\n\n// Łączymy istniejącą treść z nowym wierszem, upewniając się, że jest tylko jedna nowa linia\nconst finalContent = currentContent.trim() + '\\n' + newRow;\n\n// Kodujemy finalną treść z powrotem do Base64\nconst base64Content = Buffer.from(finalContent).toString('base64');\n\n// Zwracamy wszystko, czego potrzebuje następny nod\nconst result = {\n  base64Content: base64Content,\n  sha: fileSha // Zwracamy sha (może być null, jeśli plik jest nowy)\n};\n\nreturn result;"
      },
      "id": "44c3009b-e842-4602-a4e5-fcc3eacf9039",
      "name": "2. Przygotuj nową treść pliku",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [
        -1120,
        -432
      ]
    },
    {
      "parameters": {
        "resource": "file",
        "operation": "edit",
        "owner": {
          "__rl": true,
          "value": "Wiecek-K",
          "mode": "list",
          "cachedResultName": "Wiecek-K",
          "cachedResultUrl": "https://github.com/Wiecek-K"
        },
        "repository": {
          "__rl": true,
          "value": "discord-knowledge-base-backup",
          "mode": "list",
          "cachedResultName": "discord-knowledge-base-backup",
          "cachedResultUrl": "https://github.com/Wiecek-K/discord-knowledge-base-backup"
        },
        "filePath": "={{ $('WebHook: Save').item.json.body.channel_name }}/linki.md",
        "fileContent": "={{ $('2. Przygotuj nową treść pliku').item.json.base64Content }}",
        "commitMessage": "=Zasób dodany przez {{ $('WebHook: Save').item.json.body.proposer_name }}",
        "additionalParameters": {
          "branch": {
            "branch": "dev"
          }
        }
      },
      "id": "3cd8601c-f61c-488e-85d0-760c6bd0d6ba",
      "name": "3. Zapisz zmiany w gałęzi 'dev'",
      "type": "n8n-nodes-base.github",
      "typeVersion": 1.1,
      "position": [
        -880,
        -432
      ],
      "webhookId": "cc72baaf-94f6-4539-8b2d-43e81090c26e",
      "credentials": {
        "githubApi": {
          "id": "9Jm1ye1aJP8vV0bT",
          "name": "GitHub account"
        }
      }
    },
    {
      "parameters": {
        "resource": "message",
        "guildId": {
          "__rl": true,
          "value": "={{ $('WebHook: Save').item.json.body.server_id }}",
          "mode": "id"
        },
        "channelId": {
          "__rl": true,
          "value": "={{ $('WebHook: Save').item.json.body.channel_id }}",
          "mode": "id"
        },
        "content": "=Gotowe! Zwój czeka na zatwierdzenie!\n",
        "options": {}
      },
      "id": "fdf1af4c-4228-4bbc-8de7-c7625a1c0b2f",
      "name": "4. Wyślij potwierdzenie na Discord",
      "type": "n8n-nodes-base.discord",
      "typeVersion": 2,
      "position": [
        -640,
        -432
      ],
      "webhookId": "a46a070e-8f5d-4ad7-b0a0-00ab375218a7",
      "credentials": {
        "discordBotApi": {
          "id": "dwyNA75geJMJ4AQV",
          "name": "Discord Bot account"
        }
      }
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "skryba-save",
        "options": {}
      },
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2.1,
      "position": [
        -1568,
        -432
      ],
      "id": "70abdd0f-249a-4176-befb-8fc3723a7a62",
      "name": "WebHook: Save",
      "webhookId": "ef473205-7140-4143-a90d-564bbccedbb7"
    }
  ],
  "connections": {
    "1. Pobierz plik .md z gałęzi 'dev'": {
      "main": [
        [
          {
            "node": "2. Przygotuj nową treść pliku",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "2. Przygotuj nową treść pliku": {
      "main": [
        [
          {
            "node": "3. Zapisz zmiany w gałęzi 'dev'",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "3. Zapisz zmiany w gałęzi 'dev'": {
      "main": [
        [
          {
            "node": "4. Wyślij potwierdzenie na Discord",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "WebHook: Save": {
      "main": [
        [
          {
            "node": "1. Pobierz plik .md z gałęzi 'dev'",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "70067eb9aa902a06a7b0b8136b4a9690f056064b103e0cba4759bfc821393b41"
  }
}
```
w jaki sposób zapisywane są wpisy w pliki .md:

<docelowy plik md>
| Link                                                                                    | Opis                                                                                                                                                                                                                                                                               |
| --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Eleven Reader](https://elevenreader.io/)                                               | Czytnik ebooków AI (możesz wybrać głos np Piotra Fronczewskiego)                                                                                                                                                                                                                   |
| [Obsidian Stats](https://www.obsidianstats.com/new "https://www.obsidianstats.com/new") | Przeglądarka pluginów Obsidian z filtrami i statystykami                                                                                                                                                                                                                           |
| [The 500 AI Agents Projects](https://github.com/ashishpatel26/500-AI-Agents-Projects)   | Zbiór starannie dobranych przypadków użycia agentów AI w różnych branżach, prezentujących praktyczne zastosowania i linkujących do projektów open source do wdrożenia. Odkryj, jak agenci AI transformują branże takie jak opieka zdrowotna, finanse, edukacja i wiele innych! 🤖✨ |
| [link](https://www.youtube.com/watch?v=mC4GQTy5sqk) | fajna muzyka   taki medivaln tavern |
| [strona do grania w szachy](https://www.chess.com/) | strona do grania w szachy |
| [https://www.youtube.com/watch?...](https://www.youtube.com/watch?v=mC4GQTy5sqk) | fajna muzyka   taki medivaln tavern |
</docelowy plik md>
- przy parsowaniu i zapisywaniu do bazy chcę żeby do opisu był doklejany tekst wyświetlany zamiast ulr ([The 500 AI Agents Projects],  [Obsidian Stats]) A obiekt w bazie zawierał url oraz utworzony w ten sposób opis

Cel na dzisiaj: Uruchomienie bazy wektorowej i zaimplementowanie wyszukiwania


