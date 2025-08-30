from PySide6.QtWidgets import QMainWindow

from lab_manager.dashboard import Dashboard

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._dashboard_widget = Dashboard()
        self.setCentralWidget(self._dashboard_widget)
        self.setWindowTitle("Lab Manager")
        self.resize(960, 540)