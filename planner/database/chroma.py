from typing import Literal, Optional, Union
from chromadb import Client, EmbeddingFunction
from chromadb.utils import embedding_functions

from utils.utils import read_key_value_pairs

class ChromaDBInterface():
    def __init__(
        self,
        embedding_model: Union[EmbeddingFunction, Literal["default", "gemini"], None] = None,
        embedding_model_api_key: Optional[str] = None,
        db_path: Optional[str] = None,  # TODO: add db_path support
    ) -> None:
        self.client = Client()
        self.collection = self.client.get_or_create_collection(
            name="local_knowledge", 
            embedding_function=self._set_embedding_func(
                embedding_model, embedding_model_api_key
            )
        )
    
    def _set_embedding_func(
        self, 
        embedding: Union[EmbeddingFunction, Literal["default", "gemini"], None] = None,
        embedding_model_api_key: Optional[str] = None,
    ) -> Optional[EmbeddingFunction]:
        if embedding is None:
            return embedding_functions.DefaultEmbeddingFunction()
        elif isinstance(embedding, EmbeddingFunction):
            embedding_func = embedding
        elif embedding == "gemini":
            embedding_func = embedding_functions.GoogleGenerativeAiEmbeddingFunction( # type: ignore
                api_key=embedding_model_api_key, task_type="RETRIEVAL_QUERY"
            )
        return embedding_func
    
    def upsert(self, documents: list[str], ids: list[str]):
        self.collection.add(documents=documents, ids=ids)
    
    def query(self, query_texts: Union[str, list], n_results: int = 1):
        return self.collection.query(query_texts=query_texts, n_results=n_results)


if __name__ == "__main__":
    import uuid
    a = uuid.uuid4()
    db = ChromaDBInterface(embedding_model=None, embedding_model_api_key=read_key_value_pairs("key.env")["GEMINI_API_KEY"])
    db.upsert(
        # documents
        [
            "机の上にりんごが２つあります", 
            "キッチンには２つの机があります",
            "りんごが台所にあります",
            "冷蔵庫の中にりんごがあります",
            "キッチンに冷蔵庫があります",
            "キッチンに台所があります",
            "ユーザーは"
        ], 
        
        # ids
        [
            f"{uuid.uuid4()}",
            f"{uuid.uuid4()}",
            f"{uuid.uuid4()}",
            f"{uuid.uuid4()}",
            f"{uuid.uuid4()}",
            f"{uuid.uuid4()}",
        ]
    )


    r = db.query(["机の上のりんご"], n_results=3)
    print(r)