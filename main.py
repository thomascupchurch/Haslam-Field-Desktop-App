import sys
import fitz  # PyMuPDF
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QTabWidget, QWidget, QVBoxLayout, QPushButton, QFileDialog, QScrollArea, QLineEdit, QListWidget, QListWidgetItem, QDateEdit, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtWidgets import QHBoxLayout, QLineEdit
from PyQt5.QtWidgets import QComboBox
import pyqtgraph as pg

class PDFViewer(QWidget):
    pdf_loaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.scroll_area = QScrollArea(self)
        self.label = QLabel('No PDF loaded')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(600, 800)
        self.label.setScaledContents(True)
        self.scroll_area.setWidget(self.label)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        self.open_btn = QPushButton('Open PDF')
        self.open_btn.clicked.connect(self.open_pdf)
        layout.addWidget(self.open_btn)
        # Navigation and jump controls
        self.prev_btn = QPushButton('Previous Page')
        self.next_btn = QPushButton('Next Page')
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)
        # Page number display and jump
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
        layout.addLayout(self.page_control_layout)
        self.setLayout(layout)
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


    def on_gantt_bar_clicked(self, event):
        pos = event.scenePos()
        vb = self.plot_widget.getPlotItem().getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        mx, my = mouse_point.x(), mouse_point.y()
        # Find the closest bar (task) to the click
        if not self.tasks:
            return
        base_date = min([task['start'] for task in self.tasks])
        for i, task in enumerate(self.tasks):
            start_days = base_date.daysTo(task['start'])
            end_days = base_date.daysTo(task['end'])
            bar_center = (start_days + end_days) / 2
            bar_y = i + 1
            bar_width = end_days - start_days
            # Check if click is within the bar's rectangle
            if (mx >= start_days and mx <= end_days) and (abs(my - bar_y) <= 0.4):
                # Jump to associated PDF page if possible
                page = task.get('page')
                if page is not None:
                    mw = self.parentWidget()
                    while mw and not hasattr(mw, 'pdf_viewer'):
                        mw = mw.parentWidget()
                    if mw and hasattr(mw, 'pdf_viewer'):
                        mw.pdf_viewer.show_page(page)
                break
    def __init__(self):
        super().__init__()
        today = QDate.currentDate()
        self.tasks = [
            {'name': 'Task 1', 'start': today, 'end': today.addDays(3), 'parent': None},
            {'name': 'Task 2', 'start': today.addDays(2), 'end': today.addDays(6), 'parent': None},
            {'name': 'Task 3', 'start': today.addDays(5), 'end': today.addDays(8), 'parent': 'Task 1'},
        ]
        layout = QVBoxLayout()
        self.label = QLabel('Gantt Chart Builder')
        layout.addWidget(self.label)
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
        self.duration_input.setPlaceholderText('Duration (days)')
        self.parent_dropdown = QComboBox()
        self.parent_dropdown.addItem('No Parent')
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText('PDF Page #')
        self.page_input.setFixedWidth(60)
        form_layout.addWidget(self.page_input)
        self.add_btn = QPushButton('Add Task')
        self.add_btn.clicked.connect(self.add_task)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.start_input)
        form_layout.addWidget(self.end_input)
        form_layout.addWidget(self.duration_input)
        form_layout.addWidget(self.parent_dropdown)
        form_layout.addWidget(self.add_btn)

        layout.addLayout(form_layout)
        # Task list widget
        self.task_list = QListWidget()
        self.task_list.itemClicked.connect(self.load_task_for_edit)
        layout.addWidget(self.task_list)
        # Edit and delete buttons
        edit_layout = QHBoxLayout()
        self.edit_btn = QPushButton('Edit Task')
        self.edit_btn.clicked.connect(self.edit_task)
        self.delete_btn = QPushButton('Delete Task')
        self.delete_btn.clicked.connect(self.delete_task)
        edit_layout.addWidget(self.edit_btn)
        edit_layout.addWidget(self.delete_btn)
        layout.addLayout(edit_layout)

        # Gantt chart plot widget
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def update_duration(self):
        start = self.start_input.date()
        end = self.end_input.date()
        duration = start.daysTo(end)
        self.duration_input.setText(str(duration))
        # Optionally, update end date if duration is changed directly (not implemented here)

    def refresh_task_list(self):
        # Clear and repopulate the task list with hierarchy and durations
        self.task_list.clear()
        for task in self.tasks:
            start_str = task['start'].toString('yyyy-MM-dd')
            end_str = task['end'].toString('yyyy-MM-dd')
            duration = task['start'].daysTo(task['end'])
            prefix = '    ' * (task.get('indent', 0))
            page = (task.get('page') or 0) + 1 if task.get('page') is not None else ''
            self.task_list.addItem(f"{prefix}{task['name']} (Pg {page}, {start_str} - {end_str}, {duration} days)")

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
            bar = pg.BarGraphItem(x=x, height=0.8, width=width, y=y, brush='#FF8200')
            self.plot_widget.addItem(bar)
            # Add task name labels centered in each bar
            for i, task in enumerate(self.tasks):
                label = pg.TextItem(task['name'], anchor=(0.5, 0.5), color='k')
                label.setFont(pg.Qt.QtGui.QFont('Arial', 10))
                # Center label at the bar's center
                label.setPos((x[i]), y[i])
                self.plot_widget.addItem(label)
        self.plot_widget.getPlotItem().getViewBox().invertY(True)
        self.plot_widget.setYRange(0, len(self.tasks) + 1)
        self.plot_widget.setXRange(-1, max([base_date.daysTo(t['end']) for t in self.tasks]+[1])+1)
        self.plot_widget.setLabel('left', 'Tasks')
        self.plot_widget.setLabel('bottom', f'Days from {base_date.toString("yyyy-MM-dd")}')

    def add_task(self):
        name = self.name_input.text().strip()
        start = self.start_input.date()
        end = self.end_input.date()
        parent = self.parent_dropdown.currentText()
        page = self.page_input.text().strip()
        try:
            page_num = int(page) - 1 if page else None
        except ValueError:
            page_num = None
        if parent == 'No Parent':
            parent = None
        if name and end > start:
            self.tasks.append({'name': name, 'start': start, 'end': end, 'parent': parent, 'page': page_num})
            self.refresh_task_list()
            self.refresh_gantt_chart()
            self.name_input.clear()
            self.start_input.setDate(start)
            self.end_input.setDate(end)
            self.page_input.clear()
            self.update_duration()

    def load_task_for_edit(self, item):
        idx = self.task_list.currentRow()
        # Flatten tasks for index lookup
        flat_tasks = []
        def add_flat(tasks, parent=None):
            for t in [t for t in tasks if t.get('parent') == parent]:
                flat_tasks.append(t)
                add_flat(tasks, t['name'])
        add_flat(self.tasks)
        if idx >= 0 and idx < len(flat_tasks):
            task = flat_tasks[idx]
            self.name_input.setText(task['name'])
            self.start_input.setDate(task['start'])
            self.end_input.setDate(task['end'])
            self.update_duration()
            self.page_input.setText(str((task.get('page') or 0) + 1) if task.get('page') is not None else '')
            # Jump to associated PDF page if possible
            mw = self.parentWidget()
            while mw and not hasattr(mw, 'pdf_viewer'):
                mw = mw.parentWidget()
            if mw and hasattr(mw, 'pdf_viewer') and task.get('page') is not None:
                mw.pdf_viewer.show_page(task['page'])
            # Set parent dropdown
            if task.get('parent'):
                ix = self.parent_dropdown.findText(task['parent'])
                self.parent_dropdown.setCurrentIndex(ix if ix >= 0 else 0)
            else:
                self.parent_dropdown.setCurrentIndex(0)
            self.selected_index = self.tasks.index(task)

    def edit_task(self):
        idx = self.selected_index
        if idx is not None and 0 <= idx < len(self.tasks):
            name = self.name_input.text().strip()
            start = self.start_input.date()
            end = self.end_input.date()
            parent = self.parent_dropdown.currentText()
            page = self.page_input.text().strip()
            try:
                page_num = int(page) - 1 if page else None
            except ValueError:
                page_num = None
            if parent == 'No Parent':
                parent = None
            if name and end > start:
                self.tasks[idx] = {'name': name, 'start': start, 'end': end, 'parent': parent}
                self.refresh_task_list()
                self.refresh_gantt_chart()
                self.name_input.clear()
                self.start_input.setDate(start)
                self.end_input.setDate(end)
                self.page_input.clear()
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


class MainView(QWidget):
    def __init__(self, pdf_viewer, gantt_chart):
        super().__init__()
        layout = QVBoxLayout()
    splitter = QSplitter()
    pdf_viewer.setMinimumSize(400, 400)
    gantt_chart.setMinimumSize(400, 400)
    splitter.addWidget(pdf_viewer)
    splitter.addWidget(gantt_chart)
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 1)
    splitter.setSizes([600, 600])
    splitter.setMinimumSize(800, 400)
    layout.addWidget(splitter)
    self.setLayout(layout)

class MainWindow(QMainWindow):
    # Project save/load buttons
    def __init__(self):
        super().__init__()
    self.setWindowTitle('Haslam Field Desktop App')
    self.setGeometry(100, 100, 1000, 700)
    self.setMinimumSize(900, 600)
        self.pdf_viewer = PDFViewer()
        self.gantt_chart = GanttChartWidget()
        self.main_view = MainView(self.pdf_viewer, self.gantt_chart)
        central_widget = QWidget()
        vbox = QVBoxLayout()
        # Project save/load buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('Save Project')
        self.save_btn.clicked.connect(self.save_project)
        self.load_btn = QPushButton('Load Project')
        self.load_btn.clicked.connect(self.load_project)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.load_btn)
        vbox.addLayout(btn_layout)
        vbox.addWidget(self.main_view)
        central_widget.setLayout(vbox)
        self.setCentralWidget(central_widget)
        self._last_pdf_path = None

    def save_project(self):
        import json
        from PyQt5.QtWidgets import QFileDialog
        # Gather project data
        data = {
            'pdf_path': self._last_pdf_path,
            'tasks': [self._serialize_task(t) for t in self.gantt_chart.tasks]
        }
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Project', '', 'Project Files (*.json)')
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def load_project(self):
        import json
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, 'Load Project', '', 'Project Files (*.json)')
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Restore PDF
            pdf_path = data.get('pdf_path')
            if pdf_path:
                self.pdf_viewer.load_pdf(pdf_path)
            # Restore tasks
            tasks = [self._deserialize_task(t) for t in data.get('tasks', [])]
            self.gantt_chart.tasks = tasks
            self.gantt_chart.refresh_task_list()
            self.gantt_chart.refresh_gantt_chart()
            # No sync needed; tasks are already loaded into gantt_chart

    def _serialize_task(self, task):
        # Convert QDate to string for JSON
        t = dict(task)
        t['start'] = t['start'].toString('yyyy-MM-dd')
        t['end'] = t['end'].toString('yyyy-MM-dd')
        return t

    def _deserialize_task(self, task):
        # Convert string dates back to QDate
        t = dict(task)
        t['start'] = QDate.fromString(t['start'], 'yyyy-MM-dd')
        t['end'] = QDate.fromString(t['end'], 'yyyy-MM-dd')
        return t
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Haslam Field Desktop App')
        self.setGeometry(100, 100, 1000, 700)


    # All sync logic removed; only one view now
    def on_pdf_loaded(self, file_path):
        self._last_pdf_path = file_path

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
