# check_qdrant.py
import os
import pprint
from qdrant_client import QdrantClient

# --- Konfiguracja ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "baza_wiedzy")

print(f"LOG: Łączenie z serwerem Qdrant pod adresem: {QDRANT_HOST}:{QDRANT_PORT}")

try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print("LOG: Pomyślnie połączono z Qdrant.")

    print(f"LOG: Sprawdzanie kolekcji '{COLLECTION_NAME}'...")
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    
    points_count = collection_info.points_count
    print(f"\n✅ W kolekcji '{COLLECTION_NAME}' znajduje się {points_count} punktów (wektorów).")

    if points_count > 0:
        print("\n📄 Podgląd pierwszych 5 punktów w bazie:")
        # Używamy 'scroll' do pobrania kilku pierwszych punktów
        records, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=5,
            with_payload=True,
            with_vectors=False # Nie potrzebujemy wektorów do podglądu
        )
        pprint.pprint(records)

except Exception as e:
    print(f"\n❌ BŁĄD: Nie udało się połączyć lub odczytać danych z Qdrant.")
    print(f"   Szczegóły błędu: {e}")
    print("   Upewnij się, że kontenery Docker są uruchomione (`docker compose up ...`).")