import json
import os
from pathlib import Path

from embeddings import embed_text, embed_image_bytes
from vector_store import FaissStore

TEXT_EXTENSIONS = {'.txt', '.md'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}


def ingest_text_files(store: FaissStore, text_dir: Path):
    for path in sorted(text_dir.glob('*')):
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        content = path.read_text(encoding='utf-8').strip()
        if not content:
            continue
        title = path.stem
        vector = embed_text(content)
        item_id = f'text:{path.name}'
        metadata = {
            'title': title,
            'content': content,
            'type': 'text',
            'source': str(path.name),
        }
        store.add(item_id, vector, metadata)
        print(f'Indexed text: {path.name}')


def ingest_image_files(store: FaissStore, image_dir: Path):
    metadata_map = {}
    meta_file = image_dir / 'image_metadata.json'
    if meta_file.exists():
        metadata_map = json.loads(meta_file.read_text(encoding='utf-8'))

    for path in sorted(image_dir.glob('*')):
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        data = path.read_bytes()
        vector = embed_image_bytes(data)
        item_id = f'image:{path.name}'
        metadata = {
            'title': metadata_map.get(path.name, {}).get('title', path.stem),
            'caption': metadata_map.get(path.name, {}).get('caption', ''),
            'filename': path.name,
            'type': 'image',
            'source': str(path.name),
        }
        store.add(item_id, vector, metadata)
        print(f'Indexed image: {path.name}')


def main():
    base = Path(__file__).parent
    store = FaissStore(path=base / 'store', load_existing=False)
    print('Cleared existing FAISS store')
    ingest_text_files(store, base / 'data' / 'text')
    ingest_image_files(store, base / 'data' / 'images')
    print(f'Total documents indexed: {store.count()}')


if __name__ == '__main__':
    main()
