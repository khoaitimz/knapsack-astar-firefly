"""TV4 form and asynchronous solver controller."""
from __future__ import annotations
import json
from dataclasses import asdict
from algorithms.astar import solve_astar
from algorithms.firefly import FireflyConfig, solve_firefly
from core.dataset import generate_dataset, load_dataset_json, load_dataset_csv

try:
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QFormLayout, QSpinBox, QDoubleSpinBox, QPushButton, QLabel, QTableWidget,
        QTableWidgetItem, QFileDialog, QMessageBox, QPlainTextEdit)
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    class QThread:
        def __init__(self, parent=None): pass
    class QMainWindow:
        def __init__(self, parent=None):
            raise RuntimeError('Install PySide6 to use the GUI')
    class Signal:
        def __init__(self, *args): self.slots = []
        def connect(self, slot): self.slots.append(slot)
        def emit(self, *args):
            for slot in self.slots: slot(*args)


class SolverWorker(QThread):
    # Do not shadow QThread.finished: completion and payload have different lifetimes.
    result_ready = Signal(object)
    error = Signal(str)
    def __init__(self, problem, algorithm='astar', firefly_config=None,
                 astar_time_limit_sec=5.0, astar_max_expanded_nodes=100000, parent=None):
        super().__init__(parent)
        if not PYSIDE6_AVAILABLE:
            self.result_ready, self.error = Signal(object), Signal(str)
        self.problem, self.algorithm, self.firefly_config = problem, algorithm, firefly_config
        self.astar_time_limit_sec = astar_time_limit_sec
        self.astar_max_expanded_nodes = astar_max_expanded_nodes

    def run(self):
        try:
            if self.algorithm == 'astar':
                result = solve_astar(self.problem, time_limit_sec=self.astar_time_limit_sec,
                                     max_expanded_nodes=self.astar_max_expanded_nodes)
            elif self.algorithm == 'firefly':
                result = solve_firefly(self.problem, config=self.firefly_config)
            else:
                raise ValueError(f'Unknown algorithm: {self.algorithm}')
            self.result_ready.emit(result)
        except Exception as exc:
            self.error.emit(f'{type(exc).__name__}: {exc}')


class KnapsackMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.problem, self.worker = None, None
        self.results = []
        self.setWindowTitle('Ứng dụng thuật toán A* và thuật toán đom đóm (Firefly Algorithm) cho bài toán cái túi (Knapsack problem)')
        self.resize(1100, 800)
        from PySide6.QtGui import QFont, QFontDatabase
        import sys
        if sys.platform == 'win32':
            from pathlib import Path
            import os
            font_path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'segoeui.ttf'
            if font_path.is_file():
                QFontDatabase.addApplicationFont(str(font_path))
        self.setFont(QFont('Segoe UI', 10))
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        form = QFormLayout()
        layout.addLayout(form)
        def integer(label, low, high, default):
            widget = QSpinBox(); widget.setRange(low, high); widget.setValue(default)
            form.addRow(label, widget)
            return widget
        def decimal(label, low, high, default):
            widget = QDoubleSpinBox(); widget.setRange(low, high); widget.setDecimals(3); widget.setValue(default)
            form.addRow(label, widget)
            return widget
        self.count = integer('Số vật', 1, 10000, 30)
        self.ratio = decimal('Tỷ lệ sức chứa / tổng khối lượng', .001, 1, .5)
        self.seed = integer('Seed', 0, 2147483000, 42)
        self.limit = decimal('Giới hạn mỗi thuật toán (giây)', .01, 60, 2)
        self.nodes = integer('Giới hạn nút A*', 1, 10000000, 100000)
        self.population = integer('Số đom đóm', 2, 200, 20)
        self.iterations = integer('Số vòng FA', 1, 10000, 100)
        self.alpha = decimal('Alpha', 0, 10, .5)
        self.decay = decimal('Alpha decay', .001, 1, .98)
        self.beta = decimal('Beta0', 0, 10, 1)
        self.gamma = decimal('Gamma', 0, 10, 1)
        buttons = QHBoxLayout(); layout.addLayout(buttons)
        self.controls = []
        for text, callback in [('Sinh dữ liệu', self.generate), ('Nạp JSON/CSV', self.load),
                ('Chạy A*', lambda: self.run_solver('astar')), ('Chạy FA', lambda: self.run_solver('firefly')),
                ('Xuất kết quả JSON', self.export)]:
            button = QPushButton(text); button.clicked.connect(callback); buttons.addWidget(button)
            self.controls.append(button)
        self.status = QLabel('Sẵn sàng'); layout.addWidget(self.status)
        self.items = QTableWidget(0, 3); self.items.setHorizontalHeaderLabels(['ID', 'Giá trị', 'Khối lượng'])
        from PySide6.QtWidgets import QAbstractItemView
        self.items.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.items)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['Thuật toán', 'Giá trị', 'Khối lượng', 'Hợp lệ', 'ms', 'Trạng thái'])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        self.details = QPlainTextEdit(); self.details.setReadOnly(True); layout.addWidget(self.details)
        self.generate()

    def generate(self):
        self.set_problem(generate_dataset(self.count.value(), capacity_ratio=self.ratio.value(), seed=self.seed.value()))

    def set_problem(self, problem):
        self.problem = problem; self.results = []; self.table.setRowCount(0); self.details.clear()
        self.items.setRowCount(problem.num_items)
        for row, item in enumerate(problem.items):
            for col, value in enumerate((item.id, item.value, item.weight)):
                self.items.setItem(row, col, QTableWidgetItem(str(value)))
        self.status.setText(f'{problem.name}: {problem.num_items} vật; sức chứa {problem.capacity}')

    def load(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Nạp dữ liệu', '', 'Dataset (*.json *.csv)')
        if path:
            try:
                self.set_problem(load_dataset_csv(path) if path.lower().endswith('.csv') else load_dataset_json(path))
            except Exception as exc: self.on_solver_error(str(exc))

    def run_solver(self, algorithm):
        if self.problem is None or (self.worker is not None and self.worker.isRunning()): return
        cfg = FireflyConfig(population_size=self.population.value(), max_iterations=self.iterations.value(),
            alpha=self.alpha.value(), alpha_decay=self.decay.value(), beta0=self.beta.value(),
            gamma=self.gamma.value(), seed=self.seed.value(), time_limit_sec=self.limit.value())
        self.worker = SolverWorker(self.problem, algorithm, cfg, self.limit.value(), self.nodes.value(), self)
        self.worker.result_ready.connect(self.on_solver_finished)
        self.worker.error.connect(self.on_solver_error)
        self.worker.finished.connect(self.worker_finished)
        for button in self.controls: button.setEnabled(False)
        self.status.setText(f'Đang chạy {algorithm}…')
        self.worker.start()

    def worker_finished(self):
        for button in self.controls: button.setEnabled(True)
        self.worker.deleteLater(); self.worker = None

    def on_solver_finished(self, result):
        self.results.append(asdict(result))
        row = self.table.rowCount(); self.table.insertRow(row)
        for col, value in enumerate((result.algorithm_name, result.total_value, result.total_weight,
                                    result.is_feasible, result.execution_time_ms, result.status)):
            self.table.setItem(row, col, QTableWidgetItem(str(value)))
        ids = [self.problem.items[i].id for i in result.selected_indices]
        self.details.setPlainText('Vật được chọn: ' + ', '.join(ids) + '\n' + json.dumps(result.metrics, indent=2))
        self.status.setText('Hoàn tất. Chỉ status=optimal xác nhận tối ưu; xem trạng thái khi hết giới hạn.')

    def on_solver_error(self, message):
        self.status.setText(message)
        QMessageBox.warning(self, 'Không thể chạy', message)

    def export(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Xuất kết quả', 'solution.json', 'JSON (*.json)')
        if path:
            try:
                from pathlib import Path
                payload = dict(problem=dict(name=self.problem.name, capacity=self.problem.capacity,
                    items=[asdict(item) for item in self.problem.items]), results=self.results)
                Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
            except Exception as exc: self.on_solver_error(str(exc))

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            self.status.setText('Đợi thuật toán kết thúc theo giới hạn trước khi đóng.')
            event.ignore()
        else: event.accept()
