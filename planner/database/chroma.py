from typing import Literal, Optional, Union
from chromadb import Client, Collection
from chromadb import Documents, EmbeddingFunction, Embeddings

import google.generativeai as genai


class GoogleGenerativeAiEmbeddingFunction(EmbeddingFunction[Documents]):
    ############################################
    # google gemini embedding function
    # https://github.com/chroma-core/chroma/blob/main/chromadb/utils/embedding_functions/google_embedding_function.py
    ############################################
    
    """To use this EmbeddingFunction, you must have the google.generativeai Python package installed and have a Google API key."""

    """Use RETRIEVAL_DOCUMENT for the task_type for embedding, and RETRIEVAL_QUERY for the task_type for retrieval."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "models/embedding-001",
        task_type: str = "RETRIEVAL_DOCUMENT",
    ):
        if not api_key:
            raise ValueError("Please provide a Google API key.")

        if not model_name:
            raise ValueError("Please provide the model name.")

        try:
            import google.generativeai as genai
        except ImportError:
            raise ValueError(
                "The Google Generative AI python package is not installed. Please install it with `pip install google-generativeai`"
            )

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model_name
        self._task_type = task_type
        self._task_title = None
        if self._task_type == "RETRIEVAL_DOCUMENT":
            self._task_title = "Embedding of single string"

    def __call__(self, input: Documents) -> Embeddings:
        # print(self._task_type)
        # import json
        # print(
        #         json.dumps(
        #             [
        #                 f"{self._genai.embed_content(model=self._model_name,content=text,task_type=self._task_type,title=self._task_title,)['embedding'][0:6]}" for text in input
        #             ],
        #             indent=4,
        #             ensure_ascii=False,
        #         )
        # )
        return [
            self._genai.embed_content(
                model=self._model_name,
                content=text,
                task_type=self._task_type,
                title=self._task_title,
            )["embedding"]
            for text in input
        ]
    
    
class ChromaDBWithGemini():
    def __init__(
        self,
        embedding_model: str,
        embedding_model_api_key: str,
        db_path: Optional[str] = None,  # TODO: add db_path support
    ) -> None:
        """
        
        Args:
            embedding_model: str
            embedding_model_api_key: str
            db_path: Optional[str]  # Not Supported
        """
        self._retrieval_doc_ef = GoogleGenerativeAiEmbeddingFunction(embedding_model_api_key, embedding_model, task_type="RETRIEVAL_DOCUMENT")
        self._retrieval_query_ef = GoogleGenerativeAiEmbeddingFunction(embedding_model_api_key, embedding_model, task_type="RETRIEVAL_QUERY")
        self._client = Client()
        self._collection: Collection = self._client.get_or_create_collection(
            name="local_knowledge", 
            embedding_function=self._retrieval_doc_ef, # type: ignore
        )
    
    def upsert(self, documents: list[str], ids: list[str]):
        self._collection.add(documents=documents, ids=ids)
            
    def query(self, query_texts: list[str], n_results: int = 1):
        return self._collection.query(query_embeddings=self._retrieval_query_ef(query_texts), n_results=n_results)


if __name__ == "__main__":
    import uuid
    l = [
            "There is one desk in the kitchen.",
            "Tanaka and Maeda are having a conversation in the living room.",
            "There are shoes at the entrance.",
            "There are two desks in the living room.",
            "There is a TV in the living room.",
            "There is a living room next to the kitchen",
        ]
    
    db = ChromaDBWithGemini(embedding_model="models/text-embedding-004", embedding_model_api_key="AIzaSyAuGyhqc1sKSVqBQI6mN7lJd9LDVvY0Z_I")
    db.upsert(
        # documents
        l,
        # ids
        [str(uuid.uuid4()) for _ in range(len(l))]
    )

    import json
    r = db.query([input("入力: ")], n_results=2)
    print("\n", json.dumps(r, ensure_ascii=False, indent=4))
    #print(db._collection.peek())
    
    # Where is the kitchen located?
    # Where is the room with the two desks?
    # Who is Maeda talking to?
    # Where is the room with one desk?