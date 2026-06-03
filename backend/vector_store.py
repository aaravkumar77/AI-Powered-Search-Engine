import json
import os
from typing import Any, Dict, List

import faiss
import numpy as np

class FaissStore:
    def __init__(self, dim: int = 512, path: str = "store"):
        self.dim = dim
        self.path = path
        self.index_path = os.path.join(path, "index.faiss")
        self.meta_path = os.path.join(path, "metadata.json")
        self.ids_path = os.path.join(path, "ids.json")
        os.makedirs(path, exist_ok=True)

        if os.path.exists(self.index_path) and os.path.exists(self.meta_path) and os.path.exists(self.ids_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            with open(self.ids_path, "r", encoding="utf-8") as f:
                self.ids = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.metadata = {}
            self.ids = []
            self._save()

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)
        with open(self.ids_path, "w", encoding="utf-8") as f:
            json.dump(self.ids, f, indent=2)

    def add(self, item_id: str, vector: Any, metadata: Dict[str, Any]):
        vector = np.array(vector, dtype="float32").reshape(1, -1)
        if vector.shape[1] != self.dim:
            raise ValueError(f"Vector dimension {vector.shape[1]} does not match store dimension {self.dim}")

        self.index.add(vector)
        self.ids.append(item_id)
        self.metadata[item_id] = metadata
        self._save()

    def search(self, query_vector: Any, top_k: int = 5) -> List[Dict[str, Any]]:
        query = np.array(query_vector, dtype="float32").reshape(1, -1)
        if query.shape[1] != self.dim:
            raise ValueError(f"Query vector dimension {query.shape[1]} does not match store dimension {self.dim}")

        distances, indices = self.index.search(query, top_k)
        results = []
        for score, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.ids):
                continue
            item_id = self.ids[idx]
            results.append({
                "id": item_id,
                "score": float(score),
                "metadata": self.metadata.get(item_id, {}),
            })
        return results

    def count(self) -> int:
        return self.index.ntotal

    def list_meta(self) -> Dict[str, Any]:
        return self.metadata
