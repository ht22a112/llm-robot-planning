from typing import Optional, List, Literal, Dict, Any
from planner.database.data_type import Location, JobRecord, TaskRecord

from logger.logger import LLMRobotPlannerLogSystem
log = LLMRobotPlannerLogSystem()

class MemoryDatabase():
    def __init__(self):
        self.records = {}
        self.current_job: Optional[JobRecord] = None

from planner.database.sqlite import SQLiteInterface
from planner.database.sqlite import LocationKnowledge, ObjectKnowledge, ActionHistory
from planner.database.chroma import ChromaDBWithGemini

class DatabaseManager():
    def __init__(self):
        db_path = "planner/database/db/test.db"
        self._memory_db = MemoryDatabase()
        self._sqlite_interface = SQLiteInterface(db_path)
        
        #
        self._action_history = ActionHistory(self._sqlite_interface)
        self._location_knowledge = LocationKnowledge(self._sqlite_interface)
        #self.obj_db = ObjectKnowledge(self._sqlite_interface)
        
        #
        from utils.utils import read_key_value_pairs
        self._document_db = ChromaDBWithGemini(
            embedding_model="models/text-embedding-004",
            embedding_model_api_key=read_key_value_pairs("key.env")["GEMINI_API_KEY"],
            db_path=db_path
        )
        
                
    def start_new_job(self, instruction: str, tasks: List[TaskRecord]):
        """
        Args:
            instruction: str ユーザーからの指示（最初にロボットに与える命令）
        Returns:
            None
        """
        self._memory_db.current_job = JobRecord(
            content=instruction,
            details="",
            tasks=tasks
        )
        
    def get_current_job(self) -> Optional[JobRecord]:
        return self._memory_db.current_job
    
    def log_robot_action(
        self,
        action: str,
        status: Literal["success", "failure"],
        details: Optional[str],
        x: Optional[float],
        y: Optional[float],
        z: Optional[float],
        timestamp: Optional[float] = None
    ):
        self._action_history.log_robot_action(
            action=action,
            status=status,
            details=details,
            x=x,
            y=y,
            z=z,
            timestamp=timestamp
        )
    
    def add_location_knowledge(
        self,
        location_id: str,
        location_name: str,
        description: str,
        x: float,
        y: float,
        z: float
    ):
        self._location_knowledge.add(
            location_id=location_id,
            location_name=location_name,
            description=description,
            x=x,
            y=y,
            z=z
        )
        
    def get_all_actions(self) -> List[Dict[str, Any]]:
        return self._action_history.get_all()

    def get_all_known_locations(self) -> List[Location]:
        return self._location_knowledge.get_all()
    
    
    def query_document(self, query_text: str, n_results: int = 1, distance_threshold: Optional[float] = 1) -> List[str]:
        query_results = self._document_db.query([query_text], n_results)
        l = []
        if query_results["documents"] and query_results["distances"]:
            for document, distance in zip(query_results["documents"][0], query_results["distances"][0]):
                if distance_threshold is None or distance < distance_threshold:
                    l.append(document)
        return l
        
    
    def init_helper(self):
        """テスト用初期化メソッド"""
        
        with log.span("Database initialization") as span:
            span.input("initialize database")
            
            # TODO: あとで削除 テスト用
            self.add_location_knowledge(
                location_id="玄関_001",
                location_name="玄関",
                description="家の玄関",
                x=1.0,
                y=2.0,
                z=0.0)
            self.add_location_knowledge(
                location_id="キッチン_001",
                location_name="キッチン",
                description="家のキッチン",
                x=4.0,
                y=5.0,
                z=0.0)
            self.add_location_knowledge(
                location_id="トイレ_001",
                location_name="トイレ",
                description="家のトイレ",
                x=7.0,
                y=8.0,
                z=0.0)
            
            import uuid
            l = [
                    "There is one desk in the kitchen.",
                    "Tanaka and Maeda are having a conversation in the living room.",
                    "There are shoes at the entrance.",
                    "There are two desks in the living room.",
                    "There is a TV in the living room.",
                    "There is a living room next to the kitchen",
                    "Mr. Tanaka works as an engineer at a tech company.",
                    "Mr. Tanaka enjoys hiking on weekends and exploring nature.",
                    "Mr. Tanaka is fluent in English and Japanese.",
                    "Mr. Tanaka has a collection of vintage vinyl records, primarily jazz and rock.",
                    "Mr. Tanaka studied mechanical engineering at a university in Tokyo.",
                    "Mr. Tanaka is known for his expertise in robotics and artificial intelligence.",
                    "Mr. Tanaka regularly volunteers at a local animal shelter.",
                    "Mr. Tanaka is an avid reader and especially enjoys historical fiction.",
                    "Mr. Tanaka has traveled to over 15 countries, including Italy, Canada, and South Africa.",
                    "Mr. Tanaka plays the guitar and occasionally performs at local cafes.",
            ]
            self._document_db.upsert(
                l,
                [
                    uuid.uuid4().hex for _ in range(len(l))
                ]
            )
            
            span.output("database initialized")
        
    
    