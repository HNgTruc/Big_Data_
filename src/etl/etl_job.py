"""CLI entry point. Submit to the cluster (see infra/README.md):

    spark-submit ... /opt/spark/work-dir/src/etl/etl_job.py --dataset orders_500k
"""
import argparse
import sys
from pathlib import Path

# spark-submit runs this file as a script, so make `src.etl` importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.etl import pipeline, session  # noqa: E402
from src.etl.cleaning import JOIN_STRATEGIES  # noqa: E402


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", required=True, help="folder under <root>/raw/, e.g. orders_500k")
    p.add_argument("--storage-root", default="s3a://bigdata")
    p.add_argument("--run-label", help="output folder / metrics file name (default: dataset)")
    p.add_argument("--join-strategy", choices=JOIN_STRATEGIES, default="auto")
    p.add_argument("--shuffle-partitions", type=int, default=8)
    p.add_argument("--no-aqe", action="store_true", help="disable adaptive query execution")
    p.add_argument("--no-auto-broadcast", action="store_true", help="set autoBroadcastJoinThreshold=-1")
    p.add_argument("--metrics-dir", default="/opt/spark/work-dir/results/metrics")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    spark = session.build_session(args.storage_root, args.shuffle_partitions,
                                  aqe=not args.no_aqe, auto_broadcast=not args.no_auto_broadcast)
    cfg = pipeline.RunConfig(dataset=args.dataset, storage_root=args.storage_root, run_label=args.run_label,
                             join_strategy=args.join_strategy, metrics_dir=args.metrics_dir)
    metrics = pipeline.run(spark, cfg)
    print(f"ETL_OK processing_seconds_total={metrics['processing_seconds_total']} "
          f"stages={metrics['stage_seconds']}")
    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
