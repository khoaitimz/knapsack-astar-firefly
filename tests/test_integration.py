"""TV4 integration checks: measurements, failure isolation and real Qt lifecycle."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core.knapsack import Item, KnapsackProblem, SolutionResult
from experiments.benchmark import run_benchmark, summarize_results, export_benchmark_results
from algorithms.firefly import FireflyConfig
from gui.main_window import PYSIDE6_AVAILABLE, SolverWorker, KnapsackMainWindow


def solution(value=20, status='optimal'):
    return SolutionResult('astar', [1], [0, 1], value, 8, True, 1.5, status, {})


class TestBenchmarkPipeline(unittest.TestCase):
    def setUp(self):
        self.problem = KnapsackProblem([Item(10, 5), Item(20, 8)], 10, 'integration')

    def test_measurements_seed_and_exports(self):
        with patch('experiments.benchmark.solve_astar', return_value=solution()), patch(
                'experiments.benchmark.solve_firefly', return_value=solution(status='feasible')) as fa:
            rows = run_benchmark([self.problem], FireflyConfig(seed=123), fa_runs=3)
        self.assertEqual([c.args[1].seed for c in fa.call_args_list], [123, 124, 125])
        self.assertEqual([r['gap_percent'] for r in rows], [0, 0, 0, 0])
        summary = summarize_results(rows)[1]
        self.assertEqual(summary['valid'], 3)
        self.assertEqual(summary['value_std'], 0)
        with tempfile.TemporaryDirectory() as folder:
            paths = export_benchmark_results(rows, folder)
            self.assertEqual(json.loads(Path(paths['json_path']).read_text()), rows)
            self.assertEqual(len(Path(paths['csv_path']).read_text().splitlines()), 5)

    def test_pending_is_not_a_measurement(self):
        with patch('experiments.benchmark.solve_astar', side_effect=NotImplementedError('pending')), patch(
                'experiments.benchmark.solve_firefly', side_effect=RuntimeError('failed')):
            rows = run_benchmark([self.problem], fa_runs=2)
        self.assertEqual(rows[0]['status'], 'pending_implementation')
        self.assertIsNone(rows[0]['total_value'])
        self.assertTrue(all(s['valid'] == 0 and s['value_mean'] is None for s in summarize_results(rows)))

    def test_no_optimal_reference_after_timeout(self):
        with patch('experiments.benchmark.solve_astar', return_value=solution(status='time_limit')), patch(
                'experiments.benchmark.solve_firefly', return_value=solution(status='feasible')):
            rows = run_benchmark([self.problem], fa_runs=1)
        self.assertTrue(all(r['gap_percent'] is None for r in rows))

    def test_inconsistent_result_is_error(self):
        with patch('experiments.benchmark.solve_astar', return_value=solution(value=999)), patch(
                'experiments.benchmark.solve_firefly', return_value=solution(status='feasible')):
            rows = run_benchmark([self.problem], fa_runs=1)
        self.assertEqual(rows[0]['status'], 'error')
        self.assertIsNone(rows[0]['execution_time_ms'])

    def test_invalid_and_empty_export(self):
        for count in (0, -1, 1.5, True):
            with self.assertRaises(ValueError): run_benchmark([self.problem], fa_runs=count)
        with self.assertRaises(ValueError): run_benchmark([])
        with tempfile.TemporaryDirectory() as folder:
            paths = export_benchmark_results([], folder)
            self.assertTrue(Path(paths['csv_path']).exists())
            self.assertEqual(json.loads(Path(paths['json_path']).read_text()), [])


@unittest.skipUnless(PYSIDE6_AVAILABLE, 'PySide6 not installed')
class TestQtIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_form_and_thread_completion(self):
        from PySide6.QtCore import QEventLoop, QTimer
        window = KnapsackMainWindow()
        window.set_problem(KnapsackProblem([Item(10, 5), Item(20, 8)], 10))
        loop = QEventLoop()
        with patch('gui.main_window.solve_astar', return_value=solution()):
            window.run_solver('astar')
            worker = window.worker
            self.assertFalse(window.controls[0].isEnabled())
            worker.finished.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)
            loop.exec()
            self.app.processEvents()
        self.assertEqual(len(window.results), 1)
        self.assertEqual(window.table.rowCount(), 1)
        self.assertIsNone(window.worker)
        self.assertTrue(window.controls[0].isEnabled())
        window.close()

    def test_worker_error_signal(self):
        worker = SolverWorker(KnapsackProblem([Item(1, 1)], 1), 'unknown')
        errors = []
        worker.error.connect(errors.append)
        worker.run()
        self.assertIn('Unknown algorithm', errors[0])

if __name__ == '__main__': unittest.main()
