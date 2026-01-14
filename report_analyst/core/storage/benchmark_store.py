import hashlib
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ...models.benchmark import (
    BenchmarkDataset,
    BenchmarkDatasetContent,
    BenchmarkEvaluation,
    EvaluationMetrics,
    HumanAnnotation,
    RetrievalConfig,
)

logger = logging.getLogger(__name__)


class BenchmarkStore:
    """Handle database operations for benchmarking data"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_dataset(self, dataset: BenchmarkDatasetContent, file_path: str) -> int:
        """Save a benchmark dataset to the database"""
        with sqlite3.connect(self.db_path) as conn:
            # Insert dataset metadata
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO benchmark_datasets 
                (dataset_id, name, description, version, question_set, file_path, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    dataset.dataset_id,
                    dataset.name,
                    dataset.description,
                    dataset.version,
                    dataset.question_set,
                    file_path,
                ),
            )

            # Clear existing ground truth data for this dataset
            conn.execute(
                "DELETE FROM ground_truth_chunks WHERE dataset_id = ?",
                (dataset.dataset_id,),
            )

            # Insert ground truth chunks
            for question in dataset.questions:
                for chunk in question.ground_truth_chunks:
                    conn.execute(
                        """
                        INSERT INTO ground_truth_chunks 
                        (dataset_id, question_id, chunk_id, relevance_score, is_evidence, evidence_order, annotation_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            dataset.dataset_id,
                            question.question_id,
                            chunk.chunk_id,
                            chunk.relevance_score,
                            chunk.is_evidence,
                            chunk.evidence_order,
                            chunk.annotation_notes,
                        ),
                    )

            conn.commit()
            logger.info(
                f"Saved dataset {dataset.dataset_id} with {len(dataset.questions)} questions"
            )
            return cursor.lastrowid

    def get_dataset(self, dataset_id: str) -> Optional[BenchmarkDataset]:
        """Retrieve a benchmark dataset by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM benchmark_datasets WHERE dataset_id = ?
            """,
                (dataset_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return BenchmarkDataset(
                dataset_id=row["dataset_id"],
                name=row["name"],
                description=row["description"] or None,
                version=row["version"] or None,
                question_set=row["question_set"] or None,
                file_path=row["file_path"] or None,
                created_at=(
                    datetime.fromisoformat(row["created_at"])
                    if row["created_at"]
                    else None
                ),
                updated_at=(
                    datetime.fromisoformat(row["updated_at"])
                    if row["updated_at"]
                    else None
                ),
                source="database",
            )

    def list_datasets(self) -> List[BenchmarkDataset]:
        """List all available benchmark datasets"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM benchmark_datasets ORDER BY created_at DESC
            """
            )

            datasets = []
            for row in cursor.fetchall():
                datasets.append(
                    BenchmarkDataset(
                        dataset_id=row["dataset_id"],
                        name=row["name"],
                        description=row["description"] or None,
                        version=row["version"] or None,
                        question_set=row["question_set"] or None,
                        source="database",
                        file_path=row["file_path"],
                        created_at=(
                            datetime.fromisoformat(row["created_at"])
                            if row["created_at"]
                            else None
                        ),
                        updated_at=(
                            datetime.fromisoformat(row["updated_at"])
                            if row["updated_at"]
                            else None
                        ),
                    )
                )

            return datasets

    def get_ground_truth(self, dataset_id: str) -> Dict[str, Dict[str, float]]:
        """Get ground truth data for a dataset"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT question_id, chunk_id, relevance_score 
                FROM ground_truth_chunks 
                WHERE dataset_id = ?
            """,
                (dataset_id,),
            )

            ground_truth = {}
            for row in cursor.fetchall():
                question_id = row["question_id"]
                if question_id not in ground_truth:
                    ground_truth[question_id] = {}
                ground_truth[question_id][row["chunk_id"]] = row["relevance_score"]

            return ground_truth

    def save_evaluation(self, evaluation: BenchmarkEvaluation) -> int:
        """Save an evaluation result to the database"""
        config_json = evaluation.retrieval_config.model_dump_json()
        config_hash = hashlib.sha256(config_json.encode()).hexdigest()[:16]
        metrics_json = evaluation.evaluation_metrics.model_dump_json()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO benchmark_evaluations 
                (dataset_id, evaluation_name, config_hash, retrieval_config, evaluation_metrics)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    evaluation.dataset_id,
                    evaluation.evaluation_name,
                    config_hash,
                    config_json,
                    metrics_json,
                ),
            )

            conn.commit()
            evaluation_id = cursor.lastrowid
            logger.info(
                f"Saved evaluation {evaluation.evaluation_name} with ID {evaluation_id}"
            )
            return evaluation_id

    def get_evaluation(self, evaluation_id: int) -> Optional[BenchmarkEvaluation]:
        """Retrieve an evaluation by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM benchmark_evaluations WHERE id = ?
            """,
                (evaluation_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            config_dict = json.loads(row["retrieval_config"])
            metrics_dict = json.loads(row["evaluation_metrics"])

            return BenchmarkEvaluation(
                id=row["id"],
                dataset_id=row["dataset_id"],
                evaluation_name=row["evaluation_name"],
                config_hash=row["config_hash"],
                retrieval_config=RetrievalConfig(**config_dict),
                evaluation_metrics=EvaluationMetrics(**metrics_dict),
                created_at=(
                    datetime.fromisoformat(row["created_at"])
                    if row["created_at"]
                    else None
                ),
            )

    def list_evaluations(
        self, dataset_id: Optional[str] = None
    ) -> List[BenchmarkEvaluation]:
        """List evaluations, optionally filtered by dataset"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if dataset_id:
                cursor = conn.execute(
                    """
                    SELECT * FROM benchmark_evaluations 
                    WHERE dataset_id = ? 
                    ORDER BY created_at DESC
                """,
                    (dataset_id,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM benchmark_evaluations 
                    ORDER BY created_at DESC
                """
                )

            evaluations = []
            for row in cursor.fetchall():
                config_dict = json.loads(row["retrieval_config"])
                metrics_dict = json.loads(row["evaluation_metrics"])

                evaluations.append(
                    BenchmarkEvaluation(
                        id=row["id"],
                        dataset_id=row["dataset_id"],
                        evaluation_name=row["evaluation_name"],
                        config_hash=row["config_hash"],
                        retrieval_config=RetrievalConfig(**config_dict),
                        evaluation_metrics=EvaluationMetrics(**metrics_dict),
                        created_at=(
                            datetime.fromisoformat(row["created_at"])
                            if row["created_at"]
                            else None
                        ),
                    )
                )

            return evaluations

    def save_annotation(self, annotation: HumanAnnotation) -> int:
        """Save a human annotation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO human_annotations 
                (evaluation_id, question_id, chunk_id, human_relevance_score, 
                 human_is_evidence, human_evidence_order, annotation_notes, annotator_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    annotation.evaluation_id,
                    annotation.question_id,
                    annotation.chunk_id,
                    annotation.human_relevance_score,
                    annotation.human_is_evidence,
                    annotation.human_evidence_order,
                    annotation.annotation_notes,
                    annotation.annotator_id,
                ),
            )

            conn.commit()
            return cursor.lastrowid

    def get_annotations(self, evaluation_id: int) -> List[HumanAnnotation]:
        """Get all annotations for an evaluation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM human_annotations 
                WHERE evaluation_id = ? 
                ORDER BY created_at DESC
            """,
                (evaluation_id,),
            )

            annotations = []
            for row in cursor.fetchall():
                annotations.append(
                    HumanAnnotation(
                        id=row["id"],
                        evaluation_id=row["evaluation_id"],
                        question_id=row["question_id"],
                        chunk_id=row["chunk_id"],
                        human_relevance_score=row["human_relevance_score"],
                        human_is_evidence=row["human_is_evidence"],
                        human_evidence_order=row["human_evidence_order"],
                        annotation_notes=row["annotation_notes"],
                        annotator_id=row["annotator_id"],
                        created_at=(
                            datetime.fromisoformat(row["created_at"])
                            if row["created_at"]
                            else None
                        ),
                    )
                )

            return annotations

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset and all related data"""
        with sqlite3.connect(self.db_path) as conn:
            # Delete in order due to foreign key constraints
            conn.execute(
                "DELETE FROM human_annotations WHERE evaluation_id IN (SELECT id FROM benchmark_evaluations WHERE dataset_id = ?)",
                (dataset_id,),
            )
            conn.execute(
                "DELETE FROM benchmark_evaluations WHERE dataset_id = ?", (dataset_id,)
            )
            conn.execute(
                "DELETE FROM ground_truth_chunks WHERE dataset_id = ?", (dataset_id,)
            )
            cursor = conn.execute(
                "DELETE FROM benchmark_datasets WHERE dataset_id = ?", (dataset_id,)
            )

            conn.commit()
            return cursor.rowcount > 0
