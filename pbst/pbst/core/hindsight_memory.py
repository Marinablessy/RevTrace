"""Hindsight memory utilities for learning from prior proposals."""
from hindsight_client import Hindsight

from config import (
    HINDSIGHT_URL,
    HINDSIGHT_API_KEY,
    HINDSIGHT_BANK_ID
)


class HindsightMemory:

    def __init__(self):

        self.bank_id = HINDSIGHT_BANK_ID

        self.client = Hindsight(
            base_url=HINDSIGHT_URL,
            api_key=HINDSIGHT_API_KEY
        )

        self.bank_initialized = False


    def initialize(self):

        if self.bank_initialized:
            return

        try:

            self.client.create_bank(
                bank_id=self.bank_id,

                reflect_mission=(
                    "You are the organizational memory advisor "
                    "for an RFP response team. Analyze historical "
                    "organizational knowledge, previous proposals, "
                    "case studies, policies and outcomes. "
                    "Distinguish documented facts from assumptions. "
                    "Never invent organizational capabilities."
                ),

                retain_mission=(
                    "Extract durable organizational knowledge from "
                    "company documents. Preserve capabilities, "
                    "limitations, customer context, proposal outcomes, "
                    "evidence, policies and lessons learned."
                ),

                retain_extraction_mode="verbose",

                enable_text_search=True,
                enable_temporal_retrieval=True,
                enable_graph_retrieval=True,
                enable_reranking=True
            )

        except Exception as e:

            # The bank may already exist.
            if "already exists" not in str(e).lower():
                raise

        self.bank_initialized = True


    def retain_document(
        self,
        content,
        filename,
        document_type,
        outcome="Unknown",
        customer="Unknown"
    ):

        self.initialize()

        metadata = {
            "filename": filename,
            "document_type": document_type,
            "outcome": outcome,
            "customer": customer
        }

        tags = [
            f"document_type:{document_type}",
            f"outcome:{outcome.lower()}"
        ]

        return self.client.retain(
            bank_id=self.bank_id,
            content=content,

            context=(
                f"Organizational document: {document_type}. "
                f"Outcome: {outcome}. "
                f"Customer/industry: {customer}."
            ),

            document_id=filename,

            metadata=metadata,

            tags=tags,

            retain_async=False
        )


    def recall(self, query):

        self.initialize()

        response = self.client.recall(
            bank_id=self.bank_id,
            query=query,
            max_tokens=5000,
            budget="mid",
            include_chunks=True
        )

        results = []

        for result in response.results:

            results.append(
                {
                    "id": getattr(
                        result,
                        "id",
                        ""
                    ),

                    "text": getattr(
                        result,
                        "text",
                        ""
                    ),

                    "type": getattr(
                        result,
                        "type",
                        ""
                    ),

                    "context": getattr(
                        result,
                        "context",
                        ""
                    ),

                    "metadata": getattr(
                        result,
                        "metadata",
                        {}
                    )
                }
            )

        return results


    def reflect(
        self,
        query,
        context=None
    ):

        self.initialize()

        response = self.client.reflect(
            bank_id=self.bank_id,
            query=query,
            context=context,
            budget="mid",
            max_tokens=5000
        )

        return getattr(
            response,
            "text",
            str(response)
        )