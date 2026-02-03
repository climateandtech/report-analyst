import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yaml

from ...models.benchmark import (
    BenchmarkDataset,
    BenchmarkDatasetContent,
    BenchmarkQuestion,
    GroundTruthChunk,
)

logger = logging.getLogger(__name__)


class DatasetValidationError(Exception):
    """Raised when dataset validation fails"""

    pass


class DatasetLoader:
    """Loads and validates benchmark datasets"""

    def __init__(self):
        self.supported_formats = [".yaml", ".yml", ".json", ".csv"]

    def load_dataset(self, file_path: str, dataset_id: Optional[str] = None, 
                     dataset_name: Optional[str] = None, 
                     dataset_description: Optional[str] = None,
                     question_set: Optional[str] = None) -> BenchmarkDatasetContent:
        """
        Load and validate a benchmark dataset from file.
        
        Args:
            file_path: Path to the dataset file
            dataset_id: Optional dataset ID (required for CSV, optional for YAML/JSON)
            dataset_name: Optional dataset name (required for CSV, optional for YAML/JSON)
            dataset_description: Optional description (required for CSV, optional for YAML/JSON)
            question_set: Optional question set identifier (required for CSV, optional for YAML/JSON)
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. Supported: {self.supported_formats}"
            )

        # Handle CSV files differently
        if path.suffix.lower() == ".csv":
            return self._load_csv_dataset(path, dataset_id, dataset_name, dataset_description, question_set)

        # Load raw data for YAML/JSON
        raw_data = self._load_raw_data(path)

        # Validate and parse
        dataset = self._validate_and_parse(raw_data)

        logger.info(
            f"Successfully loaded dataset '{dataset.name}' with {len(dataset.questions)} questions"
        )
        return dataset

    def _load_raw_data(self, path: Path) -> Dict:
        """Load raw data from file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                if path.suffix.lower() in [".yaml", ".yml"]:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            raise DatasetValidationError(f"Failed to load file {path}: {e}")

    def _validate_and_parse(self, raw_data: Dict) -> BenchmarkDatasetContent:
        """Validate raw data and parse into structured format"""
        try:
            # Validate required top-level fields
            required_fields = [
                "dataset_id",
                "name",
                "description",
                "version",
                "question_set",
                "questions",
            ]
            for field in required_fields:
                if field not in raw_data:
                    raise DatasetValidationError(f"Missing required field: {field}")

            # Parse questions
            questions = []
            for q_data in raw_data["questions"]:
                question = self._parse_question(q_data)
                questions.append(question)

            return BenchmarkDatasetContent(
                dataset_id=raw_data["dataset_id"],
                name=raw_data["name"],
                description=raw_data["description"],
                version=raw_data["version"],
                question_set=raw_data["question_set"],
                created_at=raw_data.get("created_at", ""),
                questions=questions,
            )

        except Exception as e:
            raise DatasetValidationError(f"Dataset validation failed: {e}")

    def _parse_question(self, q_data: Dict) -> BenchmarkQuestion:
        """Parse a single question from raw data"""
        if "question_id" not in q_data:
            raise DatasetValidationError("Question missing 'question_id'")
        if "question_text" not in q_data:
            raise DatasetValidationError("Question missing 'question_text'")
        if "ground_truth_chunks" not in q_data:
            raise DatasetValidationError("Question missing 'ground_truth_chunks'")

        # Parse ground truth chunks
        chunks = []
        for chunk_data in q_data["ground_truth_chunks"]:
            chunk = self._parse_ground_truth_chunk(chunk_data)
            chunks.append(chunk)

        return BenchmarkQuestion(
            question_id=q_data["question_id"],
            question_text=q_data["question_text"],
            ground_truth_chunks=chunks,
        )

    def _parse_ground_truth_chunk(self, chunk_data: Dict) -> GroundTruthChunk:
        """Parse a ground truth chunk from raw data"""
        required_fields = ["chunk_id", "relevance_score", "is_evidence"]
        for field in required_fields:
            if field not in chunk_data:
                raise DatasetValidationError(f"Ground truth chunk missing '{field}'")

        # Validate relevance score
        score = chunk_data["relevance_score"]
        if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
            raise DatasetValidationError(
                f"Invalid relevance_score: {score}. Must be between 0.0 and 1.0"
            )

        return GroundTruthChunk(
            chunk_id=chunk_data["chunk_id"],
            relevance_score=float(score),
            is_evidence=bool(chunk_data["is_evidence"]),
            evidence_order=chunk_data.get("evidence_order"),
            annotation_notes=chunk_data.get("annotation_notes"),
        )

    def validate_dataset_consistency(
        self, dataset: BenchmarkDatasetContent
    ) -> List[str]:
        """Validate dataset consistency and return list of warnings"""
        warnings = []

        # Check for duplicate question IDs
        question_ids = [q.question_id for q in dataset.questions]
        if len(question_ids) != len(set(question_ids)):
            warnings.append("Duplicate question IDs found")

        # Check evidence ordering
        for question in dataset.questions:
            evidence_chunks = [c for c in question.ground_truth_chunks if c.is_evidence]
            if evidence_chunks:
                orders = [
                    c.evidence_order
                    for c in evidence_chunks
                    if c.evidence_order is not None
                ]
                if len(orders) != len(set(orders)):
                    warnings.append(
                        f"Duplicate evidence orders in question {question.question_id}"
                    )

        # Check for questions without any relevant chunks
        for question in dataset.questions:
            relevant_chunks = [
                c for c in question.ground_truth_chunks if c.relevance_score > 0.0
            ]
            if not relevant_chunks:
                warnings.append(
                    f"Question {question.question_id} has no relevant chunks"
                )

        return warnings

    def generate_dataset_hash(self, dataset: BenchmarkDatasetContent) -> str:
        """Generate a hash for the dataset content"""
        # Create a deterministic string representation
        content = {
            "dataset_id": dataset.dataset_id,
            "version": dataset.version,
            "questions": [],
        }

        for question in sorted(dataset.questions, key=lambda q: q.question_id):
            q_data = {"question_id": question.question_id, "chunks": []}
            for chunk in sorted(question.ground_truth_chunks, key=lambda c: c.chunk_id):
                q_data["chunks"].append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "relevance_score": chunk.relevance_score,
                        "is_evidence": chunk.is_evidence,
                        "evidence_order": chunk.evidence_order,
                    }
                )
            content["questions"].append(q_data)

        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def _load_csv_dataset(self, path: Path, dataset_id: Optional[str] = None,
                          dataset_name: Optional[str] = None,
                          dataset_description: Optional[str] = None,
                          question_set: Optional[str] = None) -> BenchmarkDatasetContent:
        """
        Load a CSV dataset in ClimRetrieve format (report, question, paragraph, relevance).
        
        Expected CSV format:
        - report: Report identifier
        - question: Question text
        - paragraph: Paragraph/chunk text
        - relevance: Relevance score (0-3 for ClimRetrieve, or 0.0-1.0 normalized)
        """
        try:
            df = pd.read_csv(path)
            
            # Validate required columns
            required_cols = {"report", "question", "paragraph", "relevance"}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                raise DatasetValidationError(
                    f"CSV file missing required columns: {missing_cols}. "
                    f"Found columns: {list(df.columns)}"
                )
            
            # Use provided metadata or generate defaults
            if not dataset_id:
                dataset_id = f"csv_dataset_{path.stem}"
            if not dataset_name:
                dataset_name = f"CSV Dataset: {path.stem}"
            if not dataset_description:
                dataset_description = f"Ground truth dataset loaded from CSV file: {path.name}"
            if not question_set:
                question_set = "custom"
            
            # Normalize relevance scores to 0.0-1.0 range
            # ClimRetrieve uses 0-3, so we normalize: relevance / 3.0
            # If already in 0-1 range, keep as is
            df["relevance"] = pd.to_numeric(df["relevance"], errors="coerce").fillna(0)
            max_relevance = df["relevance"].max()
            if max_relevance > 1.0:
                # Assume ClimRetrieve format (0-3), normalize to 0-1
                df["relevance"] = df["relevance"] / max_relevance
            
            # Group by (report, question) to create questions
            questions = []
            question_counter = 0
            
            for (report, question_text), group_df in df.groupby(["report", "question"]):
                question_counter += 1
                question_id = f"q_{question_counter:04d}"
                
                # Create ground truth chunks from paragraphs
                ground_truth_chunks = []
                evidence_order = 1
                
                # Sort by relevance descending to assign evidence order
                sorted_group = group_df.sort_values("relevance", ascending=False)
                
                for idx, row in sorted_group.iterrows():
                    paragraph = str(row["paragraph"]).strip()
                    relevance_score = float(row["relevance"])
                    
                    # Use paragraph text as chunk_id (or hash if too long)
                    if len(paragraph) > 100:
                        chunk_id = hashlib.md5(paragraph.encode()).hexdigest()[:16]
                    else:
                        chunk_id = paragraph[:100]
                    
                    # Consider relevant if score > 0
                    is_evidence = relevance_score > 0.0
                    
                    ground_truth_chunks.append(
                        GroundTruthChunk(
                            chunk_id=chunk_id,
                            relevance_score=relevance_score,
                            is_evidence=is_evidence,
                            evidence_order=evidence_order if is_evidence else None,
                            annotation_notes=f"From CSV: report={report}, paragraph={paragraph[:50]}..."
                        )
                    )
                    
                    if is_evidence:
                        evidence_order += 1
                
                questions.append(
                    BenchmarkQuestion(
                        question_id=question_id,
                        question_text=str(question_text),
                        ground_truth_chunks=ground_truth_chunks,
                    )
                )
            
            dataset = BenchmarkDatasetContent(
                dataset_id=dataset_id,
                name=dataset_name,
                description=dataset_description,
                version="1.0",
                question_set=question_set,
                created_at="",
                questions=questions,
            )
            
            logger.info(
                f"Successfully loaded CSV dataset '{dataset.name}' with {len(dataset.questions)} questions "
                f"from {len(df)} rows"
            )
            return dataset
            
        except Exception as e:
            raise DatasetValidationError(f"Failed to load CSV dataset: {e}")
