# bot/scripts/sync_to_qdrant.py
import os
import re
import yaml
import hashlib
import pandas as pd
from tqdm import tqdm
from io import StringIO
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# --- Konfiguracja ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "baza_wiedzy")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 768))
DISTANCE_FUNCTION = os.getenv("DISTANCE_FUNCTION", "Cosine").upper()

MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
MANIFEST_PATH = '.knowledge_manifest.yml'

print("LOG: Inicjalizacja skryptu synchronizacji z Qdrant...")

# --- Inicjalizacja Klientów ---
try:
    print(f"LOG: Ładowanie modelu Sentence Transformer '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)
    print("LOG: Model załadowany.")

    print(f"LOG: Łączenie z serwerem Qdrant pod adresem: {QDRANT_HOST}:{QDRANT_PORT}")
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print("LOG: Pomyślnie połączono z Qdrant.")
except Exception as e:
    print(f"KRYTYCZNY BŁĄD: Inicjalizacja nie powiodła się. Błąd: {e}")
    exit(1)

def parse_markdown_table(file_path):
    print(f"LOG [Parser]: Parsowanie pliku '{file_path}'")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        df = pd.read_csv(StringIO(content), sep='|', skipinitialspace=True)
        df = df.dropna(axis=1, how='all').iloc[1:]
        df.columns = [col.strip() for col in df.columns]
        entries = []
        for _, row in df.iterrows():
            if 'Link' not in row or 'Opis' not in row or pd.isna(row['Link']) or pd.isna(row['Opis']):
                continue
            link_md, description_raw = row['Link'].strip(), str(row['Opis']).strip()
            match = re.search(r'\[(.*?)\]\((.*?)\)', link_md)
            link_title, url = (match.group(1), match.group(2)) if match else ("Brak tytułu", link_md)
            full_doc = f"{link_title}. {description_raw}"
            point_id = hashlib.md5(url.encode()).hexdigest()
            entries.append({
                'id': point_id,
                'document': full_doc,
                'payload': {
                    'source_file': os.path.basename(file_path),
                    'original_description': description_raw,
                    'url': url,
                    'link_title': link_title
                }
            })
        print(f"LOG [Parser]: Sparsowano {len(entries)} wpisów z '{file_path}'.")
        return entries
    except Exception as e:
        print(f"BŁĄD [Parser]: Błąd podczas parsowania {file_path}: {e}")
        return []

# --- Główna Logika ---
print("\n--- KROK 1: Tworzenie/Resetowanie kolekcji ---")
try:
    qdrant_client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=getattr(models.Distance, DISTANCE_FUNCTION))
    )
    print(f"LOG: Kolekcja '{COLLECTION_NAME}' została pomyślnie utworzona/zresetowana.")
except Exception as e:
    print(f"BŁĄD: Nie udało się utworzyć kolekcji. Błąd: {e}")
    exit(1)

print("\n--- KROK 2: Przetwarzanie plików źródłowych ---")
if not os.path.exists(MANIFEST_PATH):
    print(f"KRYTYCZNY BŁĄD: Brak pliku manifestu '{MANIFEST_PATH}'!")
    exit(1)

with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
    files_to_index = yaml.safe_load(f).get('files', [])

all_entries = []
if files_to_index:
    for file_path in files_to_index:
        if os.path.exists(file_path):
            all_entries.extend(parse_markdown_table(file_path))
        else:
            print(f"OSTRZEŻENIE: Plik '{file_path}' z manifestu nie istnieje.")
else:
    print("LOG: Manifest jest pusty. Brak plików do przetworzenia.")

print(f"LOG: Znaleziono łącznie {len(all_entries)} wpisów do zindeksowania.")

print("\n--- KROK 3: Generowanie embeddingów i wysyłanie do Qdrant ---")
if all_entries:
    print("LOG: Rozpoczynam generowanie embeddingów dla wszystkich dokumentów...")
    embeddings = model.encode([entry['document'] for entry in all_entries], show_progress_bar=True)
    print("LOG: Embeddingi wygenerowane.")

    points_to_upload = [
        models.PointStruct(
            id=entry['id'],
            vector=embedding.tolist(),
            payload=entry['payload']
        ) for entry, embedding in zip(all_entries, embeddings)
    ]

    print(f"LOG: Rozpoczynam operację UPSERT dla {len(points_to_upload)} punktów...")
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points_to_upload,
        wait=True
    )
    print("LOG: Operacja UPSERT zakończona sukcesem.")

print("\n--- Podsumowanie ---")
collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
final_count = collection_info.points_count
print(f"✅ Synchronizacja zakończona!")
print(f"   - Końcowa liczba wpisów w bazie: {final_count}")