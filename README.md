### **Dokumentacja Projektowa: Bot Wiedzy "Skryba"**

**Wersja:** 3.0 (Post-Wdrożenie na VPS)
**Data:** 17.10.2025

#### 1. Streszczenie (Executive Summary)

Projekt "Skryba" osiągnął status w pełni funkcjonalnego, wdrożonego na serwerze produkcyjnym (VPS) prototypu. Celem projektu jest stworzenie bota Discord, który centralizuje i ułatwia dostęp do firmowej bazy wiedzy.

W trakcie rozwoju podjęto kluczowe decyzje architektoniczne, w tym **migrację z platformy low-code n8n na dedykowaną aplikację w Pythonie** oraz **strategiczną zmianę bazy wektorowej z ChromaDB na Qdrant**. Decyzja o przejściu na Qdrant była podyktowana problemami konfiguracyjnymi i potrzebą posiadania bardziej niezawodnego i wydajnego rozwiązania z wbudowanym interfejsem administracyjnym.

Obecnie projekt posiada w pełni zautomatyzowany pipeline CI/CD. Zmiany w dedykowanym repozytorium z wiedzą na GitHubie automatycznie uruchamiają proces wektoryzacji i aktualizacji bazy danych na serwerze VPS. Obie kluczowe funkcjonalności – proponowanie nowych wpisów (`Zaproponuj...`) oraz wyszukiwanie semantyczne (`/odszukaj`) – są w pełni działające i przetestowane.

#### 2. Cel Projektu (Niezmieniony)

Głównym celem projektu jest rozwiązanie problemu rozproszonej wiedzy na firmowym serwerze Discord. Realizujemy to poprzez:
*   **Centralizację Wiedzy:** Utrzymanie jednego, czytelnego dla człowieka źródła prawdy w dedykowanym **REPOZYTORIUM WIEDZY** na GitHubie (pliki `.md`).
*   **Wyszukiwanie Semantyczne:** Umożliwienie intuicyjnego odnajdywania zasobów dzięki wydajnej bazie wektorowej **Qdrant**.
*   **Moderowany Proces Kontrybucji:** Zapewnienie wysokiej jakości danych przez zatwierdzanie zmian za pomocą Pull Requestów, zarządzanych przez reguły ochrony gałęzi.
*   **Naturalny Interfejs Użytkownika:** Integracja z Discordem poprzez komendy kontekstowe i okna dialogowe (Modals).

#### 3. Ewolucja Architektury

Projekt przeszedł dwie kluczowe ewolucje, które znacząco podniosły jego dojrzałość i niezawodność.

1.  **Migracja z n8n na Pythona:** Porzucono platformę low-code na rzecz w pełni programowalnego rozwiązania, co dało pełną kontrolę nad logiką, uwierzytelnianiem i obsługą błędów.
2.  **Migracja z ChromaDB na Qdrant:** W odpowiedzi na problemy konfiguracyjne i brak wbudowanych narzędzi administracyjnych w domyślnym obrazie ChromaDB, dokonano strategicznej zmiany na Qdrant. Zapewniło to stabilność, wyższą wydajność oraz doskonały interfejs webowy do monitorowania stanu bazy.

**Architektura Aktualna (Python + Qdrant):**
*   **Koncepcja:** Aplikacja bota w Pythonie jest centralnym punktem logiki. Komunikuje się z API Discorda, API GitHuba (do tworzenia PR) oraz bazą Qdrant (do wyszukiwania). Proces aktualizacji bazy jest obsługiwany przez niezależny workflow GitHub Actions.
*   **Zalety:** Modułowość, pełna kontrola, skalowalność, niezawodność i doskonałe narzędzia deweloperskie (hot-reloading).

```
+----------------+      +-----------------------------+      +-----------------+
|                |      |                             |----->|  GitHub API     |
|  Discord User  |----->|   Discord Bot (Python)      |      |  (Create PR)    |
|  (Proponuje/    |      |   (na serwerze VPS)         |      +-----------------+
|   Wyszukuje)   |      |                             |
+----------------+      |                             |      +-----------------+
                       +-----------------------------+----->|     Qdrant      |
                                                            | (Vector Search) |
                                                            | (na serwerze VPS)|
                                                            +-----------------+
                                                                     ^
                                                                     | (Aktualizacja danych)
+------------------+      +----------------------+                     |
|                  |      |                      |      +-----------------------------+
|  Kontrybutor     |----->| REPOZYTORIUM WIEDZY  |----->|    GitHub Actions Runner    |
| (Merge do main)  |      | (GitHub)             |      | (Generowanie embeddingów)   |
|                  |      |                      |      +-----------------------------+
+------------------+      +----------------------+
```

#### 4. Aktualny Stan Projektu

*   ✅ **Infrastruktura i Wdrożenie:**
    *   Serwer VPS z Debianem jest w pełni skonfigurowany z Dockerem i Docker Compose.
    *   Aplikacja (Bot + Qdrant) jest wdrożona i działa stabilnie w kontenerach.
    *   Skonfigurowano środowisko deweloperskie z automatycznym przeładowywaniem kodu (`hot-reloading`).

*   ✅ **Funkcjonalność Propozycji (`Zaproponuj...`):**
    *   **Status:** **W PEŁNI DZIAŁAJĄCA W ŚRODOWISKU PRODUKCYJNYM.**
    *   Bot, uwierzytelniony jako GitHub App, poprawnie tworzy Pull Requesty w docelowym, firmowym `REPOZYTORIUM WIEDZY`.

*   ✅ **Funkcjonalność Wyszukiwania (`/odszukaj`):**
    *   **Status:** **W PEŁNI DZIAŁAJĄCA I PRZETESTOWANA.**
    *   Bot poprawnie łączy się z bazą Qdrant, wektoryzuje zapytania i zwraca trafne wyniki.
    *   Zaimplementowano próg minimalnej trafności (`score_threshold`), aby poprawić jakość zwracanych linków.

*   ✅ **Automatyczna Synchronizacja Bazy Danych:**
    *   **Status:** **W PEŁNI ZAUTOMATYZOWANA I DZIAŁAJĄCA.**
    *   Workflow w `REPOZYTORIUM WIEDZY` jest poprawnie skonfigurowany i uruchamia się po zmianach w gałęzi `main`.
    *   Zastosowano zaawansowaną optymalizację "sparse checkout", dzięki czemu workflow pobiera tylko niezbędne pliki z `REPOZYTORIUM KODU`.
    *   Proces synchronizacji używa strategii "Wyczyść i Załaduj", co gwarantuje pełną spójność danych.

#### 5. Plan Działania (Finalizacja i Testy)

Projekt jest w fazie finalnych testów i przygotowania do oficjalnego wdrożenia.

1.  **Testy Scenariuszy Brzegowych:**
    *   **Cel:** Weryfikacja odporności systemu na różne typy zmian w danych.
    *   **Kroki:** Przeprowadzenie testów modyfikacji, usuwania wpisów oraz zarządzania plikami przez manifest, zgodnie z wcześniej ustalonym planem.

2.  **Finalizacja i Dobre Praktyki:**
    *   **Cel:** "Utwardzenie" aplikacji i przygotowanie jej do stabilnej, długoterminowej pracy.
    *   **Kroki:**
        *   Usunięcie nadmiarowych logów deweloperskich z kodu i workflow.
        *   Przełączenie komend Discorda z trybu deweloperskiego (gildia) na globalny.
        *   Aktualizacja dokumentacji `README.md` w obu repozytoriach.


