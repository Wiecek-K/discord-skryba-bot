import os
import re
import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
import yaml 

# --- Konfiguracja ---
# W GitHub Actions te wartości będą pobierane z sekretów
CHROMA_HOST = os.getenv("CHROMA_HOST", "http://chromadb:8000") # Używamy nazwy serwisu z docker-compose
COLLECTION_NAME = "baza_wiedzy"
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'

print("Inicjalizacja skryptu synchronizacji...")
# Inicjalizacja klienta ChromaDB i modelu
try:
    model = SentenceTransformer(MODEL_NAME)
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    print("Pomyślnie połączono z ChromaDB i załadowano model.")
except Exception as e:
    print(f"Krytyczny błąd podczas inicjalizacji: {e}")
    exit(1)

def parse_markdown_table(file_path):
    """
    Parsuje tabelę Markdown z pliku, łącząc tytuł linku z opisem.
    Zwraca listę słowników gotowych do przetworzenia.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Używamy pandas do inteligentnego wczytania tabeli Markdown
        # io.StringIO pozwala traktować string jako plik
        from io import StringIO
        df = pd.read_csv(StringIO(content), sep='|', skipinitialspace=True)
        
        # Czyszczenie DataFrame
        df = df.dropna(axis=1, how='all').iloc[1:] # Usuń puste kolumny i wiersz separatora '---'
        df.columns = [col.strip() for col in df.columns] # Oczyść nazwy kolumn
        
        entries = []
        for index, row in df.iterrows():
            link_md = row['Link'].strip()
            description_raw = str(row['Opis']).strip()
            
            # Wyciągnij tytuł i URL z formatowania Markdown
            match = re.search(r'\[(.*?)\]\((.*?)\)', link_md)
            if match:
                link_title = match.group(1)
                url = match.group(2)
            else:
                # Fallback, jeśli format jest nieprawidłowy
                link_title = "Brak tytułu"
                url = link_md

            # **REALIZACJA TWOJEGO ZAŁOŻENIA**
            # Łączymy tytuł linku z opisem, aby stworzyć bogatszy kontekst dla embeddingu
            full_description_for_embedding = f"{link_title}. {description_raw}"
            
            entries.append({
                'id': url,  # Używamy URL jako unikalnego ID
                'document': full_description_for_embedding,
                'metadata': {
                    'source_file': os.path.basename(file_path),
                    'original_description': description_raw,
                    'url': url,
                    'link_title': link_title
                }
            })
        return entries
    except Exception as e:
        print(f"Błąd podczas parsowania pliku {file_path}: {e}")
        return []

# --- Główna logika skryptu (ZAKTUALIZOWANA) ---
MANIFEST_PATH = '.knowledge_manifest.yml'
all_entries = []

if not os.path.exists(MANIFEST_PATH):
    print(f"Krytyczny błąd: Plik manifestu '{MANIFEST_PATH}' nie został znaleziony!")
    exit(1)

print(f"Wczytuję manifest z pliku: {MANIFEST_PATH}...")
with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
    manifest_data = yaml.safe_load(f)

files_to_index = manifest_data.get('files', [])

if not files_to_index:
    print("Manifest jest pusty. Nie znaleziono plików do przetworzenia. Zakończono.")
    exit(0)

for file_path in files_to_index:
    if os.path.exists(file_path):
        print(f"Przetwarzam plik z manifestu: {file_path}...")
        all_entries.extend(parse_markdown_table(file_path))
    else:
        print(f"Ostrzeżenie: Plik '{file_path}' z manifestu nie istnieje i został pominięty.")


# Używamy operacji upsert, która jest bezpieczna do wielokrotnego uruchamiania
collection.upsert(
    ids=[entry['id'] for entry in all_entries],
    documents=[entry['document'] for entry in all_entries],
    metadatas=[entry['metadata'] for entry in all_entries],
    # Embeddingi zostaną wygenerowane automatycznie przez ChromaDB, jeśli nie zostaną podane
    # Ale dla pełnej kontroli, wygenerujmy je sami:
    embeddings=model.encode([entry['document'] for entry in all_entries]).tolist()
)

print("Synchronizacja zakończona sukcesem!")
