import logging
from typing import List, Optional

from InstructorEmbedding import INSTRUCTOR

# Taken from another project of mine, repo_search
# https://github.com/Netruk44/repo-search/blob/main/repo_search/model_types/instructor_model.py
class InstructorModel():
    def __init__(
            self,
            model_name: Optional[str] = None,
            embedding_instruction: Optional[str] = None,
            retrieval_instruction: Optional[str] = None):
        
        self.model_name = model_name if model_name is not None else 'hkunlp/instructor-large'
        logging.debug(f'Loading Instructor model {self.model_name}')
        self.model = INSTRUCTOR(self.model_name)

        default_embedding_instruction = 'Represent the code document for retrieval: '
        self.embedding_instruction = embedding_instruction if embedding_instruction is not None else default_embedding_instruction

        default_retrieval_instruction = 'Represent the code search query for retrieving code documents matching the query: '
        self.retrieval_instruction = retrieval_instruction if retrieval_instruction is not None else default_retrieval_instruction

        logging.info("You may see warnings about sequence length being too long. These can be safely ignored.")
    
    def generate_embedding_for_document(self, chunk: str, verbose: bool = False) -> List[float]:
        return self.generate_embedding_with_instruction([[self.embedding_instruction, chunk]], verbose)

    def generate_embedding_for_query(self, chunk: str, verbose: bool = False) -> List[float]:
        return self.generate_embedding_with_instruction([[self.retrieval_instruction, chunk]], verbose)
    
    def generate_embedding_with_instruction(self, chunk: List[str], verbose: bool = False) -> List[float]:
        return self.model.encode(chunk)[0]

    def get_max_document_chunk_length(self) -> int:
        embed_document_instruction_length = len(self.tokenize(self.embedding_instruction))
        return self.model.get_max_seq_length() - embed_document_instruction_length
    
    def get_max_query_chunk_length(self) -> int:
        retrieve_document_instruction_length = len(self.tokenize(self.retrieval_instruction))
        return self.model.get_max_seq_length() - retrieve_document_instruction_length
    
    def tokenize(self, text: str) -> List[int]:
        return self.model.tokenizer.encode(text)
    
    def detokenize(self, tokens: List[int]) -> str:
        return self.model.tokenizer.decode(tokens)
    
    @staticmethod
    def get_model_type() -> str:
        return 'instructor'
    
    def get_model_name(self) -> str:
        return self.model_name