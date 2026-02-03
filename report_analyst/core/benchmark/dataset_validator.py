from dataclasses import dataclass
from typing import Set, Tuple

import pandas as pd


@dataclass
class ValidationResult:
    is_valid: bool
    can_proceed: bool
    message: str
    missing_pairs: Set[Tuple[str, str]]  # (report, question) pairs
    extra_pairs: Set[Tuple[str, str]]
    matching_pairs: Set[Tuple[str, str]]


class DatasetValidator:
    """Validate user datasets against benchmarks"""

    def validate_dataset_match(
        self,
        user_df: pd.DataFrame,
        benchmark_df: pd.DataFrame,
        strict_mode: bool = False,
        report_col: str = "report",
        question_col: str = "question",
    ) -> ValidationResult:
        """
        Validate that (report, question) pairs match between datasets.

        Args:
            user_df: User's results DataFrame
            benchmark_df: Benchmark ground truth DataFrame
            strict_mode: If True, require perfect match (for competition)
            report_col: Column name for report identifier
            question_col: Column name for question identifier

        Returns:
            ValidationResult with validation status and details
        """
        # Extract (report, question) pairs
        user_pairs = self._extract_pairs(user_df, report_col, question_col)
        benchmark_pairs = self._extract_pairs(benchmark_df, report_col, question_col)

        missing_in_user = benchmark_pairs - user_pairs
        extra_in_user = user_pairs - benchmark_pairs
        matching_pairs = user_pairs & benchmark_pairs

        if strict_mode:
            # Competition mode - must be perfect match
            if missing_in_user or extra_in_user:
                return ValidationResult(
                    is_valid=False,
                    can_proceed=False,
                    message=self._format_strict_error(missing_in_user, extra_in_user),
                    missing_pairs=missing_in_user,
                    extra_pairs=extra_in_user,
                    matching_pairs=matching_pairs,
                )
            else:
                return ValidationResult(
                    is_valid=True,
                    can_proceed=True,
                    message="Dataset matches perfectly!",
                    missing_pairs=set(),
                    extra_pairs=set(),
                    matching_pairs=matching_pairs,
                )
        else:
            # Development mode - show warnings but allow proceeding
            if missing_in_user or extra_in_user:
                return ValidationResult(
                    is_valid=False,
                    can_proceed=True,
                    message=self._format_warning(
                        missing_in_user, extra_in_user, matching_pairs
                    ),
                    missing_pairs=missing_in_user,
                    extra_pairs=extra_in_user,
                    matching_pairs=matching_pairs,
                )
            else:
                return ValidationResult(
                    is_valid=True,
                    can_proceed=True,
                    message="Dataset matches perfectly!",
                    missing_pairs=set(),
                    extra_pairs=set(),
                    matching_pairs=matching_pairs,
                )

    def _extract_pairs(
        self, df: pd.DataFrame, report_col: str, question_col: str
    ) -> Set[Tuple[str, str]]:
        """Extract unique (report, question) pairs from DataFrame"""
        return set(
            (str(row[report_col]), str(row[question_col])) for _, row in df.iterrows()
        )

    def _format_strict_error(self, missing: Set, extra: Set) -> str:
        """Format error message for strict mode"""
        return f"""
        Dataset Mismatch - Cannot Proceed
        
        Missing in your dataset: {len(missing)} (report, question) pairs
        Extra in your dataset: {len(extra)} (report, question) pairs
        
        Please ensure your dataset exactly matches the benchmark.
        """

    def _format_warning(self, missing: Set, extra: Set, matching: Set) -> str:
        """Format warning message for lenient mode"""
        return f"""
        Dataset Mismatch Detected
        
        Missing in your dataset: {len(missing)} pairs
        Extra in your dataset: {len(extra)} pairs
        Matching pairs: {len(matching)} pairs
        
        Only matching pairs will be evaluated.
        """


