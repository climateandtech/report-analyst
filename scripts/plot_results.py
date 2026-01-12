
#!/usr/bin/env python3

import sys
from pathlib import Path
import matplotlib.pyplot as plt

# Make project importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.test_climretrieve_benchmark import (
    run_climretrieve_benchmark,
    download_climretrieve_datasets,
)

def plot_all_metrics(metrics, save_path: Path | None = None) -> None:
    """
    Create a single high-quality PNG with:
      - Precision@K
      - Recall@K
      - F1@K
      - NDCG@K
      - MAP & MRR
    """

    # Prepare figure with 2x3 subplots
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    # ---- Line plots for @K metrics ----
    metric_specs = [
        ("precision_at_k", "Precision@K"),
        ("recall_at_k",    "Recall@K"),
        ("f1_at_k",        "F1@K"),
        ("ndcg_at_k",      "nDCG@K"),
    ]

    for ax, (attr_name, title) in zip(axes[:4], metric_specs):
        metric_dict = getattr(metrics, attr_name, None)
        if not metric_dict:
            ax.set_visible(False)
            continue

        k_values = sorted(metric_dict.keys())
        values = [metric_dict[k] for k in k_values]

        ax.plot(k_values, values, marker="o", linewidth=2)
        ax.set_title(title)
        ax.set_xlabel("K")
        ax.set_ylabel(title.split("@")[0])  # e.g. "Precision"
        ax.set_xticks(k_values)
        ax.grid(True, linestyle="--", alpha=0.6)

    # ---- MAP & MRR bar plot ----
    ax_bar = axes[4]
    names = ["MAP", "MRR"]
    vals = [metrics.mean_average_precision, metrics.mean_reciprocal_rank]

    ax_bar.bar(names, vals)
    ax_bar.set_title("MAP and MRR")
    ax_bar.set_ylabel("Score")
    ax_bar.set_ylim(0, 1)

    for i, v in enumerate(vals):
        ax_bar.text(i, v + 0.02, f"{v:.3f}", ha="center")

    # Last subplot can be turned off or used for legend / text
    axes[5].axis("off")

    fig.suptitle("ClimRetrieve Benchmark Metrics – Report Analyst", fontsize=16)
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=400, bbox_inches="tight")
        print(f"Saved all metrics plot to: {save_path}")
    else:
        plt.show()



def main():
    # Where to store/download datasets
    data_dir = PROJECT_ROOT / "data" / "climretrieve"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1) Download (or reuse existing) datasets and get their paths
    reference_path, input_path = download_climretrieve_datasets(data_dir)

    # 2) Run benchmark using those paths
    metrics = run_climretrieve_benchmark(
        reference_path=reference_path,
        input_path=input_path,
        k_values=[1, 3, 5, 10],
    )

    # 3) Plot recall@K
    plots_dir = PROJECT_ROOT / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    save_path = plots_dir / "all_metrics.png"
    plot_all_metrics(metrics, save_path=save_path)


if __name__ == "__main__":
    main()
