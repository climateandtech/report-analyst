from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class BenchmarkInfo:
    benchmark_id: str
    name: str
    description: str
    format: str  # "climretrieve" or "s4m"
    labels_path: Path
    version: str = "1.0"


class BenchmarkRegistry:
    """Registry for predefined benchmarks"""

    def __init__(self):
        self.benchmarks: Dict[str, BenchmarkInfo] = {}
        self._load_default_benchmarks()

    def _load_default_benchmarks(self):
        """Load default benchmarks (ClimRetrieve, etc.)"""
        climretrieve_path = (
            Path(__file__).parent
            / "climretrieve"
            / "labels"
            / "ClimRetrieve_ReportLevel_V1.csv"
        )
        if climretrieve_path.exists():
            self.benchmarks["climretrieve"] = BenchmarkInfo(
                benchmark_id="climretrieve",
                name="ClimRetrieve",
                description="ClimRetrieve Report-Level Benchmark",
                format="climretrieve",
                labels_path=climretrieve_path,
                version="1.0",
            )

    def list_benchmarks(self) -> List[BenchmarkInfo]:
        """List all available benchmarks"""
        return list(self.benchmarks.values())

    def get_benchmark(self, benchmark_id: str) -> Optional[BenchmarkInfo]:
        """Get benchmark by ID"""
        return self.benchmarks.get(benchmark_id)

    def load_benchmark_labels(self, benchmark_id: str) -> pd.DataFrame:
        """Load ground truth labels for a benchmark"""
        benchmark = self.get_benchmark(benchmark_id)
        if not benchmark:
            raise ValueError(f"Benchmark {benchmark_id} not found")

        if benchmark.format == "climretrieve":
            from .climretrieve_io import load_climretrieve_labels

            return load_climretrieve_labels(benchmark.labels_path)
        else:
            raise ValueError(f"Unsupported benchmark format: {benchmark.format}")


