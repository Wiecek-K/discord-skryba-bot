- #### 1. Streszczenie (Executive Summary)

Projekt "Skryba" ma na celu stworzenie bota Discord, który centralizuje i ułatwia dostęp do firmowej bazy wiedzy. Po udanej fazie początkowej, w której skonfigurowano całą infrastrukturę (Docker, VPS) i zaimplementowano kluczowe funkcjonalności, projekt osiągnął status działającego prototypu.

Najważniejszą zmianą w stosunku do pierwotnych założeń była **strategiczna migracja logiki biznesowej z platformy n8n do dedykowanej aplikacji w Pythonie**. Decyzja ta została podjęta w celu uzyskania większej kontroli nad złożonymi operacjami z API GitHuba, uwierzytelnianiem i obsługą błędów.

Obecnie projekt posiada w pełni działającą (w środowisku lokalnym) funkcjonalność proponowania nowych wpisów do bazy wiedzy poprzez moderowany proces Pull Request. Kolejne kroki skupią się na finalizacji funkcji wyszukiwania semantycznego oraz automatyzacji synchronizacji danych z bazą wektorową.

#### 2. Cel Projektu (Niezmieniony)

Głównym celem projektu jest rozwiązanie problemu rozproszonej wiedzy na firmowym serwerze Discord. Realizujemy to poprzez:

- **Centralizację Wiedzy:** Utrzymanie jednego, czytelnego dla człowieka źródła prawdy w repozytorium GitHub (pliki `.md`).
- **Wyszukiwanie Semantyczne:** Umożliwienie intuicyjnego odnajdywania zasobów dzięki bazie wektorowej ChromaDB.
- **Moderowany Proces Kontrybucji:** Zapewnienie wysokiej jakości danych przez zatwierdzanie zmian za pomocą Pull Requestów.
- **Naturalny Interfejs Użytkownika:** Integracja z Discordem poprzez komendy kontekstowe i okna dialogowe (Modals) dla maksymalnej wygody użytkowników.

#### 3. Ewolucja Architektury

Projekt przeszedł kluczową ewolucję od architektury opartej na low-code do rozwiązania w pełni programistycznego.

**Architektura Początkowa (n8n-centric):**

- **Koncepcja:** Bot Discord jako prosta bramka (gateway) przekazująca dane do n8n, gdzie znajdowała się cała logika (komunikacja z GitHub API, formatowanie danych).
- **Zalety:** Szybkie prototypowanie.

**Ograniczenia i Decyzja o Zmianie:**

- W trakcie implementacji okazało się, że złożoność operacji na GitHubie (tworzenie gałęzi, obsługa nieistniejących plików, tworzenie PR) oraz potrzeba solidnego uwierzytelniania (GitHub App) przekraczają możliwości wygodnej implementacji w n8n. Utrzymanie i debugowanie takiego workflow byłoby problematyczne.

**Architektura Aktualna (Python-centric):**

- **Koncepcja:** Bot Discord jest teraz **centralną aplikacją**, która zawiera całą logikę biznesową. Komunikuje się bezpośrednio z API Discorda, API GitHuba i bazą ChromaDB.
- **Zalety:** Pełna kontrola nad kodem, solidna obsługa błędów, łatwiejsze testowanie, możliwość implementacji zaawansowanych mechanizmów uwierzytelniania i większa skalowalność.

```
+----------------+      +-----------------------------+      +-----------------+
|                |      |                             |----->|  GitHub API     |
|  Discord User  |----->|   Discord Bot (Python)      |      |  (Create PR)    |
|                |      |   (Core Business Logic)     |      +-----------------+
+----------------+      |                             |
                       |                             |      +-----------------+
                       +-----------------------------+----->|    ChromaDB     |
                                                            | (Vector Search) |
                                                            +-----------------+
```

#### 4. Aktualny Stan Projektu

- ✅ **Infrastruktura i Wdrożenie:**

  - Serwer VPS z Debianem jest w pełni skonfigurowany.
  - Docker i Docker Compose działają stabilnie.
  - Plik `docker-compose.yml` jest gotowy i poprawnie uruchamia wszystkie usługi (Bot, ChromaDB). Usługa n8n została usunięta jako zbędna.

- ✅ **Funkcjonalność Propozycji (`Zaproponuj...`):**

  - **Status:** **W PEŁNI DZIAŁAJĄCA** (w środowisku lokalnym).
  - Użytkownik z rolą "Bibliotekarz" może użyć komendy kontekstowej na wiadomości.
  - Bot poprawnie wyłuskuje link i opis, prezentując je w edytowalnym oknie dialogowym (Modal).
  - Po zatwierdzeniu, bot (uwierzytelniony jako GitHub App) tworzy nową gałąź, modyfikuje plik `.md` i tworzy Pull Request.
  - Użytkownik otrzymuje na Discordzie wiadomość zwrotną z linkiem do stworzonego PR.

- 🟡 **Funkcjonalność Wyszukiwania (`/odszukaj`):**

  - **Status:** Zaimplementowana, wymaga finalnych testów.
  - Kod do obsługi komendy, łączenia się z ChromaDB, generowania embeddingu dla zapytania i formatowania wyników jest gotowy w pliku `main.py`.
  - Wymaga weryfikacji i testów end-to-end po zasileniu bazy ChromaDB danymi.

- 🟡 **Automatyczna Synchronizacja Bazy Danych:**
  - **Status:** Zaprojektowana, wymaga konfiguracji i testów.
  - Skrypt `scripts/sync_to_chroma.py` jest gotowy. Jego logika zakłada:
    1.  Parsowanie tabeli z pliku `.md`.
    2.  Dla każdego wiersza, tworzenie dokumentu do wektoryzacji poprzez połączenie tekstu z linku i opisu (np. `The 500 AI Agents Projects Zbiór starannie dobranych przypadków...`).
    3.  Użycie linku jako unikalnego ID w bazie ChromaDB.
    4.  Operacja `upsert` do aktualizacji bazy.
  - Plik workflow `.github/workflows/sync.yml` jest przygotowany do wdrożenia w repozytorium z wiedzą.

#### 5. Plan Działania na Najbliższe Dni (Priorytety)

1.  **Finalizacja i Testy Funkcji `/odszukaj`:**

    - **Cel:** Potwierdzenie pełnej funkcjonalności wyszukiwania.
    - **Kroki:**
      a. Ręcznie uruchomić skrypt `sync_to_chroma.py` na lokalnej maszynie, aby zasilić bazę ChromaDB danymi z przykładowego pliku `.md`.
      b. Uruchomić bota lokalnie.
      c. Zweryfikować widoczność komendy `/odszukaj` na serwerze (w razie problemów, odświeżyć klienta Discord `Ctrl+R` lub ponownie zaprosić bota).
      d. Przeprowadzić serię testowych zapytań i zweryfikować jakość zwracanych wyników.

2.  **Konfiguracja i Testy Workflow GitHub Actions:**

    - **Cel:** Zautomatyzowanie procesu aktualizacji bazy wektorowej.
    - **Kroki:**
      a. Dodać wymagane sekrety (`APP_ID`, `PRIVATE_KEY`, `CHROMA_HOST_IP`) do ustawień repozytorium z wiedzą (`discord-knowledge-base-backup`).
      b. Umieścić plik `.github/workflows/sync.yml` w tym repozytorium.
      c. Stworzyć i zmergować testowy Pull Request do gałęzi `main`.
      d. Obserwować wykonanie workflow w zakładce "Actions" na GitHubie.
      e. Zweryfikować logi workflow oraz sprawdzić, czy nowe dane pojawiły się w bazie ChromaDB.

3.  **Wdrożenie na Serwerze VPS:**

    - **Cel:** Przeniesienie działającej aplikacji do środowiska produkcyjnego.
    - **Kroki:**
      a. Zaktualizować kod na serwerze (`git pull`).
      b. Skonfigurować plik `.env` na serwerze z produkcyjnymi wartościami.
      c. Przebudować i uruchomić kontenery za pomocą `docker compose up --build -d`.
      d. Przeprowadzić finalne testy dymne (smoke tests) na produkcyjnym serwerze Discord.

4.  **Finalizacja i Dobre Praktyki:**
    - **Cel:** Przygotowanie bota do stabilnego działania.
    - **Kroki:**
      a. **TODO:** Zmienić synchronizację komend z serwera deweloperskiego na globalną w `main.py` (zamienić `tree.sync(guild=...)` na `await tree.sync()`).
      b. **TODO:** Usunąć nadmiarowe logi deweloperskie (`print()`) z kodu lub zamienić je na ustrukturyzowany system logowania (np. moduł `logging`).
      c. (Po migracji) Zaktualizować twardo zakodowane ścieżki repozytoriów w kodzie i plikach `.yml`.
