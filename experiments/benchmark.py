"""Reproducible TV4 benchmark; unavailable solvers never become measurements."""
from __future__ import annotations
import argparse
import csv
import json
import platform
import statistics
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from algorithms.astar import solve_astar
from algorithms.firefly import FireflyConfig, solve_firefly
from core.dataset import generate_dataset, save_dataset_json
from core.evaluation import evaluate_binary_solution
from core.knapsack import KnapsackProblem


def run_benchmark(problems, firefly_config=None, fa_runs=5,
                  astar_time_limit_sec=5.0, astar_max_expanded_nodes=100_000):
    if not problems or isinstance(fa_runs, bool) or not isinstance(fa_runs, int) or fa_runs < 1:
        raise ValueError('Need problems and an integer fa_runs >= 1')
    cfg = firefly_config or FireflyConfig()
    records = []
    for index, problem in enumerate(problems):
        reference = None
        for algorithm, run_id in [('astar', 0)] + [('firefly', i) for i in range(fa_runs)]:
            seed = (cfg.seed if cfg.seed is not None else 42) + run_id
            record = dict(problem_id=index, problem_name=problem.name, num_items=problem.num_items,
                          capacity=problem.capacity, algorithm=algorithm, run_id=run_id,
                          seed=seed if algorithm == 'firefly' else None,
                          total_value=None, total_weight=None, is_feasible=None,
                          execution_time_ms=None, status='error', error='', gap_percent=None)
            try:
                result = (solve_astar(problem, time_limit_sec=astar_time_limit_sec,
                                     max_expanded_nodes=astar_max_expanded_nodes)
                          if algorithm == 'astar' else solve_firefly(problem, replace(cfg, seed=seed)))
                value, weight, feasible = evaluate_binary_solution(problem, result.binary_vector)
                import math
                selected = [i for i, bit in enumerate(result.binary_vector) if bit]
                if (selected != result.selected_indices or not math.isclose(value, result.total_value, abs_tol=1e-7)
                        or not math.isclose(weight, result.total_weight, abs_tol=1e-7)
                        or feasible != result.is_feasible):
                    raise ValueError('Solver result contradicts independently evaluated vector')
                record.update(total_value=value, total_weight=weight, is_feasible=feasible,
                              execution_time_ms=result.execution_time_ms, status=result.status)
                if algorithm == 'astar' and result.status == 'optimal' and feasible:
                    reference = value
                if feasible and reference is not None:
                    record['gap_percent'] = (100 * (reference-value) / reference if reference else 0.0)
            except NotImplementedError as exc:
                record.update(status='pending_implementation', error=str(exc))
            except Exception as exc:
                record.update(status='error', error=f'{type(exc).__name__}: {exc}')
            records.append(record)
    return records


def summarize_results(records):
    groups = {}
    for row in records:
        groups.setdefault((row['problem_id'], row['algorithm']), []).append(row)
    summaries = []
    for (problem_id, algorithm), rows in groups.items():
        valid = [r for r in rows if r['is_feasible'] is True and r['status'] not in ('error', 'pending_implementation')]
        values = [r['total_value'] for r in valid]
        times = [r['execution_time_ms'] for r in valid]
        gaps = [r['gap_percent'] for r in valid if r['gap_percent'] is not None]
        summaries.append(dict(problem_id=problem_id, problem_name=rows[0]['problem_name'], algorithm=algorithm,
            attempted=len(rows), valid=len(valid), value_mean=statistics.mean(values) if values else None,
            value_std=statistics.stdev(values) if len(values)>1 else (0.0 if values else None),
            value_best=max(values) if values else None, time_mean_ms=statistics.mean(times) if times else None,
            time_std_ms=statistics.stdev(times) if len(times)>1 else (0.0 if times else None),
            gap_mean_percent=statistics.mean(gaps) if gaps else None,
            optimal_hits=sum(abs(g)<1e-7 for g in gaps) if gaps else None))
    return summaries


def export_benchmark_results(records, output_dir='experiments/results'):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, data in [('benchmark_records', records), ('benchmark_summary', summarize_results(records))]:
        for ext in ('json', 'csv'):
            path = out / f'{name}.{ext}'
            with path.open('w', encoding='utf-8', newline='') as stream:
                if ext == 'json':
                    json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
                elif data:
                    writer = csv.DictWriter(stream, fieldnames=list(data[0]))
                    writer.writeheader()
                    writer.writerows(data)
            paths[('' if name == 'benchmark_records' else 'summary_') + ext + '_path'] = str(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description='Compare only A* and binary Firefly')
    parser.add_argument('--output', default='experiments/results/latest')
    parser.add_argument('--runs', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--time-limit', type=float, default=2.0)
    parser.add_argument('--population', type=int, default=20)
    parser.add_argument('--iterations', type=int, default=100)
    args = parser.parse_args()
    cfg = FireflyConfig(seed=args.seed, population_size=args.population,
                        max_iterations=args.iterations, time_limit_sec=args.time_limit)
    problems = [generate_dataset(n, capacity_ratio=ratio, seed=args.seed+k,
                name=f'n{n}_r{ratio}_s{args.seed+k}')
                for n in (10, 30, 100) for ratio in (0.25, 0.5, 0.75) for k in range(3)]
    records = run_benchmark(problems, cfg, args.runs, args.time_limit)
    export_benchmark_results(records, args.output)
    out = Path(args.output)
    for i, problem in enumerate(problems):
        save_dataset_json(problem, str(out / 'datasets' / f'{i:03}.json'))
    (out / 'metadata.json').write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(), platform=platform.platform(), arguments=vars(args),
        firefly=asdict(cfg), astar_max_expanded_nodes=100000,
        protocol='A* once; FA repeated seeds; gap only with certified optimal A*; sample standard deviation'),
        indent=2), encoding='utf-8')
    incomplete = sum(r['status'] in ('error', 'pending_implementation') for r in records)
    print(f'{len(records)} attempts; {incomplete} unavailable/error; output: {out}')
    return 2 if incomplete else 0

if __name__ == '__main__':
    raise SystemExit(main())
