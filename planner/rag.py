from planner.database.database import DatabaseManager
from planner.llm.gen_ai import UnifiedAIRequestHandler
from planner.llm.parser import JsonParser
from prompts.utils import get_prompt

class RAG():
    def __init__(
        self, 
        db: DatabaseManager, 
        llm: UnifiedAIRequestHandler
    ):
        """
        Args:
            db: DatabaseManager
            llm: UnifiedAIRequestHandler
        """    
        self._db: DatabaseManager = db
        self._llm: UnifiedAIRequestHandler = llm
        self._json_parser: JsonParser = JsonParser()
        
    def query(self, query: str):
        """
        Args:
            query: str クエリの内容
        """
    
    def _retrieval_knowledges(self, task: str):
        pass
        
    def _retrieval_location(self):
        pass
        
    def _retrieval_document(self, task: str) -> list[str]:
        """
        Args:
            query: str クエリの内容
        """
        
        prompt = get_prompt(
            prompt_name="GENERATE_QUERY", 
            replacements={"task": task},
            symbol=("{{", "}}")
        )
        
        response = self._json_parser.parse(
            text=self._llm.generate_content(prompt),
            response_type="json",
            convert_type="dict"
        )

        l = []
        for query in response["query"]:
            r = self._db.query_document(query, 2)
            l.extend(r if r else [])
        print(l)
        print(set(l))
        return list(set(l))