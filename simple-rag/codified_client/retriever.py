from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle

from .codified_client import CodifiedClient, get_access_context

__all__ = ["CodifiedRetriever"]

class CodifiedRetriever(BaseRetriever):
    def __init__(self, client: CodifiedClient, delegate_retriever: BaseRetriever) -> None:
        self.client = client
        self.delegate_retriever = delegate_retriever

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        results = self.delegate_retriever._retrieve(query_bundle)
        file_ids: list[str] = [r.metadata['file id'] for r in results]
        access_context = get_access_context()
        if not access_context:
            raise Exception("access context not set")        
        allowed = self.client.check_access(file_ids, access_context["user_email"])
        filtered_results = [node for node in results if node.metadata["file id"] in allowed and allowed[node.metadata["file id"]]]
        return filtered_results