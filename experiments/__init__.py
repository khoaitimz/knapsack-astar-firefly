"""Experiment tools (lazy exports keep python -m free of double imports)."""
__all__ = ['run_benchmark', 'export_benchmark_results', 'summarize_results']
def __getattr__(name):
    if name in __all__:
        from experiments import benchmark
        return getattr(benchmark, name)
    raise AttributeError(name)
