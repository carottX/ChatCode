from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryMemory

from constants import EmbeddingsModel
from embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from typing import List, Dict, Any
import logging
from pydantic import Field


from vector_store import VectorStore

class CustomRetriever(BaseRetriever):
    """
    Custom retriever that can be used to customize document retrieval logic.
    """
    vectorstore: VectorStore = Field(description="The vector store to use")

    def __init__(self, vs):
        """
        Initialize the custom retriever with a base retriever.
        
        Args:
            base_retriever: The underlying retriever to enhance
        """
        super().__init__(vectorstore=vs)
        
    def _get_relevant_documents(
        self, query: str, *, run_manager: Any = None
    ) -> List[Document]:
        """
        Get documents relevant to the query.
        
        Args:
            query: The query to search for
            run_manager: The run manager to use
            
        Returns:
            List of relevant documents
        """
        
        # Get documents from the base retriever
        docs = self.vectorstore.db.as_retriever(k=12, filter={'type':'summary'}).invoke(query)
                
        summary_ids =  [doc.metadata["unique_id"] for doc in docs]
        real_doc = []
        for summary_id in summary_ids:
            original_doc = self.vectorstore.db.similarity_search(
                query,
                filter = {'unique_id':summary_id, 'type':'original'},
                k=2,
            )
            original_doc = [doc for doc in original_doc if doc.metadata['type'] == 'original' and doc.metadata['unique_id'] == summary_id]
            if not original_doc: logging.warning('No original doc found for {}'.format(summary_id))
            real_doc.extend(original_doc)
        return real_doc

def bootstrap(config, repo_name, embeddings_model, llm):
    """
    Initializes the necessary components for the application.

    Args:
        config (dict): Configuration dictionary containing settings for embeddings and LLM.
        repo_name (str): The name of the repository.
        embeddings_model (Embeddings, optional): Pre-initialized embeddings model. Defaults to None.

    Returns:
        tuple: A tuple containing the vector store, memory, and QA chain.
    """

    vector_store = VectorStore(repo_name, embeddings=embeddings_model.embeddings)
    vector_store.load_documents()
    
    memory = ConversationSummaryMemory(
        llm=llm.chat_model, memory_key="chat_history", return_messages=True
    )

    # customretriever = CustomRetriever(vector_store)

    qa = ConversationalRetrievalChain.from_llm(
        llm.chat_model, retriever=vector_store.db.as_retriever(search_type="mmr", search_kwargs={"k": 8}), return_source_documents=True
    )

    return memory, qa
