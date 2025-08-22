import sys
import fitz  # PyMuPDF
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QTabWidget, QWidget, QVBoxLayout, QPushButton, QFileDialog, QScrollArea, QLineEdit, QListWidget, QListWidgetItem, QDateEdit, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QDate

import pyqtgraph as pg

class PDFViewer(QWidget):
    pdf_loaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea(self)
        self.label = QLabel('No PDF loaded')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(600, 800)
        self.label.setScaledContents(True)
        self.scroll_area.setWidget(self.label)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        self.open_btn = QPushButton('Open PDF')
        self.open_btn.clicked.connect(self.open_pdf)
        self.layout.addWidget(self.open_btn)
        # Navigation and jump controls
        self.prev_btn = QPushButton('Previous Page')
        self.next_btn = QPushButton('Next Page')
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.layout.addWidget(self.prev_btn)
        self.layout.addWidget(self.next_btn)
        # Page number display and jump
        from PyQt5.QtWidgets import QHBoxLayout, QLineEdit
        self.page_control_layout = QHBoxLayout()
        self.page_label = QLabel('Page: 0 / 0')
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText('Page #')
        self.page_input.setFixedWidth(60)
        self.jump_btn = QPushButton('Jump to Page')
        self.jump_btn.clicked.connect(self.jump_to_page)
        self.page_control_layout.addWidget(self.page_label)
        self.page_control_layout.addWidget(self.page_input)
        self.page_control_layout.addWidget(self.jump_btn)
        self.layout.addLayout(self.page_control_layout)
        self.pdf_doc = None
        self.current_page = 0

    def open_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open PDF', '', 'PDF Files (*.pdf)')
        if file_path:
            self.load_pdf(file_path)

    def load_pdf(self, file_path):
        if file_path:
            try:
                self.pdf_doc = fitz.open(file_path)
                if self.pdf_doc.page_count == 0:
                    raise ValueError('PDF has no pages.')
                self.current_page = 0
                self.show_page(self.current_page)
                self.pdf_loaded.emit(file_path)
            except Exception as e:
                self.label.setText(f'Failed to load PDF: {str(e)}')
        else:
            self.label.setText('No PDF loaded')

    def show_page(self, page_number):
        try:
            if self.pdf_doc is None:
                self.label.setText('No PDF loaded')
                self.page_label.setText('Page: 0 / 0')
                return
            if page_number < 0 or page_number >= self.pdf_doc.page_count:
                self.label.setText('Page out of range')
                self.page_label.setText(f'Page: {self.current_page+1} / {self.pdf_doc.page_count}')
                return
            page = self.pdf_doc.load_page(page_number)
            pix = page.get_pixmap()
            if pix.width == 0 or pix.height == 0:
                raise ValueError('Failed to render PDF page.')
            if pix.alpha:
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888)
            else:
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            self.label.clear()
            self.label.setPixmap(pixmap)
            self.label.setMinimumSize(pix.width, pix.height)
            self.page_label.setText(f'Page: {page_number+1} / {self.pdf_doc.page_count}')
        except Exception as e:
            self.label.setText(f'Failed to display page: {str(e)}')
            if self.pdf_doc:
                self.page_label.setText(f'Page: {self.current_page+1} / {self.pdf_doc.page_count}')
            else:
                self.page_label.setText('Page: 0 / 0')

    def jump_to_page(self):
        if self.pdf_doc:
            try:
                page_num = int(self.page_input.text()) - 1
                if 0 <= page_num < self.pdf_doc.page_count:
                    self.current_page = page_num
                    self.show_page(self.current_page)
                else:
                    self.label.setText('Page out of range')
            except ValueError:
                self.label.setText('Invalid page number')

    def next_page(self):
        if self.pdf_doc and self.current_page < self.pdf_doc.page_count - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def prev_page(self):
        if self.pdf_doc and self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

class GanttChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.label = QLabel('Gantt Chart Builder')
        self.layout.addWidget(self.label)
        # Task form
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('Task Name')
        self.start_input = QDateEdit()
        self.start_input.setCalendarPopup(True)
        self.start_input.setDate(QDate.currentDate())
        self.end_input = QDateEdit()
        self.end_input.setCalendarPopup(True)
        self.end_input.setDate(QDate.currentDate().addDays(1))
        self.duration_input = QLineEdit()
        self.duration_input.setReadOnly(True)
        self.duration_input.setPlaceholderText('Duration (days)')
        self.start_input.dateChanged.connect(self.update_duration)
        self.end_input.dateChanged.connect(self.update_duration)
        self.add_btn = QPushButton('Add Task')
        self.add_btn.clicked.connect(self.add_task)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.start_input)
        form_layout.addWidget(self.end_input)
        form_layout.addWidget(self.duration_input)
        form_layout.addWidget(self.add_btn)
        self.layout.addLayout(form_layout)

    def update_duration(self):
        start = self.start_input.date()
        end = self.end_input.date()
        duration = start.daysTo(end)
        self.duration_input.setText(str(duration) if duration > 0 else "0")
        # Task list
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.load_task_for_edit)
        self.layout.addWidget(self.task_list)
        # Edit/delete controls
        edit_layout = QHBoxLayout()
        self.edit_btn = QPushButton('Edit Task')
        self.edit_btn.clicked.connect(self.edit_task)
        self.delete_btn = QPushButton('Delete Task')
        self.delete_btn.clicked.connect(self.delete_task)
        edit_layout.addWidget(self.edit_btn)
        edit_layout.addWidget(self.delete_btn)
        self.layout.addLayout(edit_layout)
        # Chart
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        # Data
        today = QDate.currentDate()
        self.tasks = [
            {'name': 'Task 1', 'start': today, 'end': today.addDays(3)},
            {'name': 'Task 2', 'start': today.addDays(2), 'end': today.addDays(6)},
            {'name': 'Task 3', 'start': today.addDays(5), 'end': today.addDays(8)},
        ]
        self.selected_index = None
        self.refresh_task_list()
        self.refresh_gantt_chart()

    def refresh_task_list(self):
        self.task_list.clear()
        for task in self.tasks:
            start_str = task['start'].toString('yyyy-MM-dd')
            end_str = task['end'].toString('yyyy-MM-dd')
            duration = task['start'].daysTo(task['end'])
            self.task_list.addItem(f"{task['name']} ({start_str} - {end_str}, {duration} days)")

    def refresh_gantt_chart(self):
        self.plot_widget.clear()
        y = []
        x = []
        width = []
        if not self.tasks:
            return
        base_date = min([task['start'] for task in self.tasks])
        for i, task in enumerate(self.tasks):
            start_days = base_date.daysTo(task['start'])
            end_days = base_date.daysTo(task['end'])
            y.append(i + 1)
            x.append((start_days + end_days) / 2)
            width.append(end_days - start_days)
        if x and y and width:
            bar = pg.BarGraphItem(x=x, height=0.8, width=width, y=y, brush='b')
            self.plot_widget.addItem(bar)
        self.plot_widget.getPlotItem().getViewBox().invertY(True)
        self.plot_widget.setYRange(0, len(self.tasks) + 1)
        self.plot_widget.setXRange(-1, max([base_date.daysTo(t['end']) for t in self.tasks]+[1])+1)
        self.plot_widget.setLabel('left', 'Tasks')
        self.plot_widget.setLabel('bottom', f'Days from {base_date.toString("yyyy-MM-dd")}')

    def add_task(self):
        name = self.name_input.text().strip()
        start = self.start_input.date()
        end = self.end_input.date()
        if name and end > start:
            self.tasks.append({'name': name, 'start': start, 'end': end})
            self.refresh_task_list()
            self.refresh_gantt_chart()
            self.name_input.clear()
            self.start_input.setDate(start)
            self.end_input.setDate(end)
            self.update_duration()

    def load_task_for_edit(self, item):
        idx = self.task_list.currentRow()
        if idx >= 0:
            task = self.tasks[idx]
            self.name_input.setText(task['name'])
            self.start_input.setDate(task['start'])
            self.end_input.setDate(task['end'])
            self.update_duration()
            self.selected_index = idx

    def edit_task(self):
        idx = self.selected_index
        if idx is not None and 0 <= idx < len(self.tasks):
            name = self.name_input.text().strip()
            start = self.start_input.date()
            end = self.end_input.date()
            if name and end > start:
                self.tasks[idx] = {'name': name, 'start': start, 'end': end}
                self.refresh_task_list()
                self.refresh_gantt_chart()
                self.name_input.clear()
                self.start_input.setDate(start)
                self.end_input.setDate(end)
                self.update_duration()
                self.selected_index = None

    def delete_task(self):
        idx = self.selected_index
        if idx is not None and 0 <= idx < len(self.tasks):
            del self.tasks[idx]
            self.refresh_task_list()
            self.refresh_gantt_chart()
            self.name_input.clear()
            self.start_input.clear()
            self.end_input.clear()
            self.selected_index = None


class CombinedView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        from PyQt5.QtWidgets import QSplitter
        splitter = QSplitter()
        self.pdf_viewer = PDFViewer()
        self.gantt_chart = GanttChartWidget()
        splitter.addWidget(self.pdf_viewer)
        splitter.addWidget(self.gantt_chart)
        splitter.setSizes([400, 400])
        layout.addWidget(splitter)
    def load_pdf(self, file_path):
        self.pdf_viewer.load_pdf(file_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Haslam Field Desktop App')
        self.setGeometry(100, 100, 1000, 700)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.pdf_viewer = PDFViewer()
        self.gantt_chart = GanttChartWidget()
        self.combined_view = CombinedView()
        self.tabs.addTab(self.pdf_viewer, 'PDF Viewer')
        self.tabs.addTab(self.gantt_chart, 'Gantt Chart')
        self.tabs.addTab(self.combined_view, 'Combined View')

        # Synchronize PDF loading
        self.pdf_viewer.pdf_loaded.connect(self.on_pdf_loaded)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self._last_pdf_path = None

    def on_pdf_loaded(self, file_path):
        self._last_pdf_path = file_path
        # If Combined View tab is selected, update its PDF viewer
        if self.tabs.currentWidget() == self.combined_view:
            self.combined_view.load_pdf(file_path)

    def on_tab_changed(self, idx):
        # If switching to Combined View and a PDF was loaded, update its PDF viewer
        if self.tabs.widget(idx) == self.combined_view and self._last_pdf_path:
            self.combined_view.load_pdf(self._last_pdf_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
