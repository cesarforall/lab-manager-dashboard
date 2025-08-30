import sys
from PySide6.QtWidgets import QApplication
from lab_manager.dashboard import Dashboard

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec())
