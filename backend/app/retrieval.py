"""
Retrieval module for MirAI Student Policy Advisor.
Configures LangChain MultiQueryRetriever with real LLM-based query expansion,
ChromaDB similarity search, and deterministic chunk deduplication.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import BaseOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever
except ImportError:
    from langchain.retrievers.multi_query import MultiQueryRetriever

from app.config import settings
from app.exceptions import RetrievalError, VectorStoreNotInitializedError
from app.vector_store import PolicyVectorStoreManager, vector_store_manager

logger = logging.getLogger("mirai.retrieval")


class LineListOutputParser(BaseOutputParser[List[str]]):
    """Parses multiline output into a list of non-empty query strings."""
    def parse(self, text: str) -> List[str]:
        lines = text.strip().split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            # Remove leading numbering like "1.", "1)", "-", "*"
            if line:
                cleaned_line = line.lstrip("0123456789.-*) ").strip()
                if cleaned_line:
                    cleaned.append(cleaned_line)
        return cleaned


MULTI_QUERY_PROMPT_TEMPLATE = """You are an AI language model assistant for a university policy information system.
Your task is to generate 3 different versions of the given student question to retrieve relevant policy documents from a vector database.
By generating multiple perspectives on the user question, your goal is to overcome limitations of distance-based similarity search.
Ensure queries include formal policy terms as well as student phrasing (e.g. 'attendance marks', 'medical leave', 'condonation', 'malpractice', 'society proposal').

Original student question: {question}

Provide these alternative questions separated by newlines (do not add numbering or preamble):"""

MULTI_QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template=MULTI_QUERY_PROMPT_TEMPLATE,
)


class PolicyRetriever:
    """
    Orchestrates MultiQueryRetriever and document deduplication over the policy vector store.
    """

    def __init__(
        self,
        vector_mgr: Optional[PolicyVectorStoreManager] = None,
        chat_model_name: Optional[str] = None,
        temperature: float = 0.0,
    ):
        self.vector_mgr = vector_mgr or vector_store_manager
        self.chat_model_name = chat_model_name or settings.GOOGLE_CHAT_MODEL
        self.temperature = temperature
        self._multi_query_retriever: Optional[MultiQueryRetriever] = None

    def get_query_expansion_llm(self) -> ChatGoogleGenerativeAI:
        """Instantiates LLM for MultiQuery expansion with temperature=0.0."""
        api_key = settings.GOOGLE_API_KEY
        return ChatGoogleGenerativeAI(
            model=self.chat_model_name,
            temperature=self.temperature,
            api_key=api_key,
        )

    def get_multi_query_retriever(self, k: int = 5) -> MultiQueryRetriever:
        """Builds or returns the MultiQueryRetriever instance."""
        if not self.vector_mgr.is_initialized():
            raise VectorStoreNotInitializedError(
                "Cannot initialize retriever: vector store is empty. Ingest the handbook first."
            )

        vector_store = self.vector_mgr.get_vector_store()
        base_retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )

        llm = self.get_query_expansion_llm()

        try:
            mq_retriever = MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=llm,
                prompt=MULTI_QUERY_PROMPT,
                parser_key="lines",
            )
            return mq_retriever
        except Exception as e:
            logger.warning(f"Could not initialize MultiQueryRetriever with custom parser: {e}. Falling back to default.")
            return MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=llm,
                prompt=MULTI_QUERY_PROMPT,
            )

    def retrieve_documents(
        self,
        question: str,
        k: int = 5,
    ) -> Tuple[List[Document], List[str]]:
        """
        Executes query expansion, retrieves documents across all sub-queries,
        and returns deduplicated documents along with generated sub-queries.
        """
        if not self.vector_mgr.is_initialized():
            raise VectorStoreNotInitializedError(
                "No policy handbook indexed. Please ingest the official handbook before querying."
            )

        sub_queries: List[str] = [question]
        try:
            # Generate sub-queries using LLM
            llm = self.get_query_expansion_llm()
            parser = LineListOutputParser()
            formatted_prompt = MULTI_QUERY_PROMPT.format(question=question)
            expansion_res = llm.invoke(formatted_prompt)
            if hasattr(expansion_res, "content") and isinstance(expansion_res.content, str):
                expanded_list = parser.parse(expansion_res.content)
                if expanded_list:
                    sub_queries.extend(expanded_list[:3])
        except Exception as e:
            logger.warning(f"Query expansion fallback to single query due to: {e}")

        # Retrieve documents across all queries with score tracking
        vector_store = self.vector_mgr.get_vector_store()
        unique_docs: Dict[str, Document] = {}

        for q in sub_queries:
            try:
                results_with_scores = vector_store.similarity_search_with_score(q, k=k)
                for doc, score in results_with_scores:
                    chunk_id = doc.metadata.get("chunk_id") or doc.page_content[:50]
                    if chunk_id not in unique_docs:
                        doc.metadata["retrieval_distance"] = round(float(score), 4)
                        unique_docs[chunk_id] = doc
            except Exception as e:
                logger.error(f"Search failed for sub-query '{q}': {e}")
                raise RetrievalError(f"Vector search failed: {e}")

        deduplicated_docs = list(unique_docs.values())
        return deduplicated_docs, sub_queries
