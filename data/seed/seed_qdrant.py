import os
import sys
import json
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Add the backend folder to sys.path so we can import config
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "backend"))

from config import settings

def chunk_rules(rules_data: dict) -> list:
    chunks = []
    
    # Process low risk F&B rules
    if "fb_pangan_olahan_kering_rendah" in rules_data:
        data = rules_data["fb_pangan_olahan_kering_rendah"]
        cat_name = data["kategori_nama"]
        
        # Chunk 1: Category general description
        chunks.append({
            "text": f"Kategori: {cat_name}. Kriteria Bisnis: {data['kriteria_bisnis']}",
            "metadata": {"category": "fb_pangan_olahan_kering_rendah", "type": "general"}
        })
        
        # Chunk per permit
        for item in data["urutan_izin"]:
            text = (
                f"Izin Usaha F&B Mikro Kering: {item['izin']} ({item['kode']}). "
                f"Wajib: {item['wajib']}. Dasar Hukum: {item['dasar_hukum']}. "
                f"Prasyarat: {item['prasyarat']}. Biaya: {item['biaya']}. "
                f"Durasi pengerjaan: {item['durasi']}. "
                f"Cara mengurus: {item['cara_urus']}"
            )
            chunks.append({
                "text": text,
                "metadata": {
                    "category": "fb_pangan_olahan_kering_rendah", 
                    "type": "permit", 
                    "permit_code": item["kode"]
                }
            })
            
    # Process high risk F&B rules
    if "fb_pangan_olahan_basah_tinggi" in rules_data:
        data = rules_data["fb_pangan_olahan_basah_tinggi"]
        cat_name = data["kategori_nama"]
        
        chunks.append({
            "text": f"Kategori: {cat_name}. Kriteria Bisnis: {data['kriteria_bisnis']}",
            "metadata": {"category": "fb_pangan_olahan_basah_tinggi", "type": "general"}
        })
        
        for item in data["urutan_izin"]:
            text = (
                f"Izin Usaha F&B Risiko Tinggi/Basah: {item['izin']} ({item['kode']}). "
                f"Wajib: {item['wajib']}. Dasar Hukum: {item['dasar_hukum']}. "
                f"Prasyarat: {item['prasyarat']}. Biaya: {item['biaya']}. "
                f"Durasi pengerjaan: {item['durasi']}. "
                f"Cara mengurus: {item['cara_urus']}"
            )
            chunks.append({
                "text": text,
                "metadata": {
                    "category": "fb_pangan_olahan_basah_tinggi", 
                    "type": "permit", 
                    "permit_code": item["kode"]
                }
            })
            
    # Process Tax rules
    if "pajak_umkm" in rules_data:
        data = rules_data["pajak_umkm"]
        cat_name = data["kategori_nama"]
        rules = data["rules"] if "rules" in data else data.get("aturan", {})
        
        text = (
          f"Perpajakan UMKM: {cat_name}. Kriteria: {data['kriteria_bisnis']}. "
          f"Tarif Pajak: {rules.get('tarif')}. Dasar Hukum: {rules.get('dasar_hukum')}. "
          f"Aturan Orang Pribadi: {rules.get('WP_Orang_Pribadi')}. "
          f"Aturan PT Perorangan: {rules.get('WP_PT_Perorangan')}. "
          f"Aturan CV, Firma, PT Umum: {rules.get('WP_CV_Firma_PT_Umum')}."
        )
        chunks.append({
            "text": text,
            "metadata": {"category": "pajak_umkm", "type": "tax"}
        })
        
    return chunks

def seed():
    print(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}...")
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    
    # Check if Qdrant is running
    try:
        # Check connection
        client.get_collections()
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        print("Please make sure Qdrant Docker container is running.")
        sys.exit(1)
        
    # Configure local embedding model via fastembed
    # This uses sentence-transformers/all-MiniLM-L6-v2 locally (it will download automatically if not cached)
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Initializing FastEmbed model: {embedding_model}...")
    client.set_model(embedding_model)
    
    collection_name = settings.QDRANT_COLLECTION
    
    # Recreate collection to ensure clean state
    print(f"Recreating collection '{collection_name}'...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=client.get_fastembed_vector_params()
    )
    
    # Read regulatory rules JSON
    rules_json_path = project_root / "data" / "regulatory_rules.json"
    print(f"Reading rules from {rules_json_path}...")
    with open(rules_json_path, "r", encoding="utf-8") as f:
        rules_data = json.load(f)
        
    chunks = chunk_rules(rules_data)
    print(f"Generated {len(chunks)} chunks for seeding.")
    
    documents = [c["text"] for c in chunks]
    payloads = [c["metadata"] for c in chunks]
    
    # Insert chunks with auto-generated embeddings
    print("Ingesting vectors and documents into Qdrant...")
    client.add(
        collection_name=collection_name,
        documents=documents,
        metadata=payloads
    )
    
    print("Seeding completed successfully!")

if __name__ == "__main__":
    seed()
