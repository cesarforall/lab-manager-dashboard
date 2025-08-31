from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtGui import QAction

from lab_manager.data.database import get_connection
from lab_manager.dashboard import Dashboard
from lab_manager.updates import UpdatesDialog

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lab Manager")
        self.resize(960, 540)

        self.conn = get_connection()

        self._dashboard_widget = Dashboard()
        self.setCentralWidget(self._dashboard_widget)

        self.create_actions()
        self.create_menus()

    def create_actions(self):
        self._quit_act = QAction("&Cerrar", self, shortcut="Ctrl+Q", statusTip="Cerrar la aplicación", triggered=self.close)

        self._open_updates_act = QAction("&Actualizaciones", self, triggered=self.open_updates_dialog)

        self._about_act = QAction("&Acerca de Lab Manager", self, triggered=self.open_about)

    def create_menus(self):
        self._edit_menu = self.menuBar().addMenu("&Archivo")
        self._edit_menu.addSeparator()
        self._edit_menu.addAction(self._quit_act)

        self._file_menu = self.menuBar().addMenu("&Herramientas")
        self._file_menu.addAction(self._open_updates_act)

        self._help_menu = self.menuBar().addMenu("&Ayuda")
        self._help_menu.addAction(self._about_act)

    def open_updates_dialog(self):
        dialog = UpdatesDialog(self.conn, self)
        dialog.exec()

    def open_about(self):
        QMessageBox.about(self, "Acerca de Lab Manager",
            """<b>Lab Manager</b><br>
            Aplicación de gestión de laboratorio.<br><br>
            Desarrollado por César Almeida<br>
            Github: <a href="https://github.com/cesarforall">GitHub</a><br>
            """)