import json
from pathlib import Path

from embeddings import embed_text, embed_image_bytes
from vector_store import FaissStore

TEXT_EXTENSIONS = {'.txt', '.md'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}


def ingest_text_files(store: FaissStore, text_dir: Path):
    for path in sorted(text_dir.rglob('*')):
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        content = path.read_text(encoding='utf-8').strip()
        if not content:
            continue
        relative_path = path.relative_to(text_dir).as_posix()
        title = path.stem
        vector = embed_text(content)
        item_id = f'text:{relative_path}'
        metadata = {
            'title': title,
            'content': content,
            'type': 'text',
            'source': relative_path,
        }
        store.add(item_id, vector, metadata)
        print(f'Indexed text: {relative_path}')


def ingest_image_files(store: FaissStore, image_dir: Path):
    metadata_map = {}
    meta_file = image_dir / 'image_metadata.json'
    if meta_file.exists():
        metadata_map = json.loads(meta_file.read_text(encoding='utf-8'))

    for path in sorted(image_dir.rglob('*')):
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        relative_path = path.relative_to(image_dir).as_posix()
        file_metadata = metadata_map.get(relative_path) or metadata_map.get(path.name, {})
        category = path.parent.name if path.parent != image_dir else ''
        default_title = category.replace('_', ' ').title() if category else path.stem
        default_caption = f'Image from the {default_title} category.' if category else ''
        data = path.read_bytes()
        vector = embed_image_bytes(data)
        item_id = f'image:{relative_path}'
        metadata = {
            'title': file_metadata.get('title', default_title),
            'caption': file_metadata.get('caption', default_caption),
            'filename': relative_path,
            'type': 'image',
            'source': relative_path,
        }
        store.add(item_id, vector, metadata)
        print(f'Indexed image: {relative_path}')


def main():
    base = Path(__file__).parent
    store = FaissStore(path=base / 'store', load_existing=False)
    print('Cleared existing FAISS store')
    ingest_text_files(store, base / 'data' / 'text')
    ingest_image_files(store, base / 'data' / 'images')
    print(f'Total documents indexed: {store.count()}')


if __name__ == '__main__':
    main()
