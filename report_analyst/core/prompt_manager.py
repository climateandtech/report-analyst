import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from llama_index.core.llms import ChatMessage, MessageRole


class PromptManager:
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)

    def get_analysis_messages(
        self, question: str, context: str, guidelines: str, chunks_data: List[Dict]
    ) -> List[ChatMessage]:
        """Generate messages for TCFD question analysis"""
        # Format chunks with numbers and scores for reference
        formatted_chunks = "\n\n".join(
            [
                f"[CHUNK {i+1}] (Relevance Score: {chunk.get('computed_score', chunk.get('relevance_score', 0.0)):.3f})\n{chunk['text']}"
                for i, chunk in enumerate(chunks_data)
            ]
        )

        return [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="You are an AI assistant in the role of a Senior Equity Analyst with expertise in climate science that analyzes companys' sustainability reports.",
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=f"""With the following extracted components of the sustainability report at hand, please analyze the question and provide a comprehensive response with evidence and scoring.

QUESTION: {question}
=========
Each chunk is shown with its relevance score (0.0-1.0). Higher scores indicate more relevant content.

{formatted_chunks}
=========

Please adhere to the following guidelines in your answer:
1. Your response must be precise, thorough, and grounded on specific extracts from the report to verify its authenticity.
2. Consider the relevance scores when selecting evidence - higher scores suggest more relevant content.
3. If you are unsure, simply acknowledge the lack of knowledge, rather than fabricating an answer.
4. Keep your ANSWER within 60 words.
5. Be skeptical to the information disclosed in the report as there might be greenwashing (exaggerating the firm's environmental responsibility). Always answer in a critical tone.
6. cheap talks are statements that are costless to make and may not necessarily reflect the true intentions or future actions of the company. Be critical for all cheap talks you discovered in the report.
7. Always acknowledge that the information provided is representing the company's view based on its report.
8. Scrutinize whether the report is grounded in quantifiable, concrete data or vague, unverifiable statements, and communicate your findings.
9. For each piece of evidence, you MUST reference the specific chunk number [CHUNK X] where it came from.
{guidelines}

IMPORTANT: Your response MUST be in valid JSON format like this example:
{{
    "ANSWER": "Your detailed analysis of the question",
    "SCORE": "Score from 0-10 indicating disclosure quality and completeness",
    "EVIDENCE": [
        {{"text": "Key evidence point", "chunk": X}},
        {{"text": "Another evidence point", "chunk": Y}}
    ],
    "GAPS": ["List of missing information or gaps in disclosure"],
    "SOURCES": [X, Y, Z]  # List of chunk numbers referenced
}}

Your FINAL_ANSWER in JSON (ensure there's no format error):""",
            ),
        ]

    def process_result(self, result: dict, results: dict, q_id: str):
        try:
            result_json = json.loads(result["result"])
            results["answers"][q_id] = result_json.get("ANSWER", "No answer provided")
            results["sources"][q_id] = result_json.get("SOURCES", [])
        except Exception as e:
            print(f"Error processing result: {e}")
            results["answers"][q_id] = "Error processing result"
            results["sources"][q_id] = []
