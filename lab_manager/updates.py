from PySide6.QtWidgets import (QDialog, QTableView, QVBoxLayout, QTabWidget, QWidget, QLineEdit,
                               QGridLayout, QLabel, QComboBox, QListWidget, QListWidgetItem,
                               QPushButton, QMessageBox, QHBoxLayout)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIntValidator
from PySide6.QtCore import Qt

from lab_manager.data import queries

class UpdatesDialog(QDialog):
    def __init__(self, conn, parent = None,):
        super().__init__(parent)
        self.setWindowTitle("Actualizaciones")
        self.setFixedSize(854, 480)

        self.conn = conn        

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Fabricante", "Modelo", "Versión", "Fecha"])

        updates = queries.get_latest_device_updates(conn)

        for row in updates:
            items = [QStandardItem(str(field)) for field in row]
            self.model.appendRow(items)
            
        self.table_widget = QTableView()
        self.table_widget.setModel(self.model)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setEditTriggers(QTableView.NoEditTriggers)
        self.table_widget.resizeColumnsToContents()

        self.new_update_widget = QWidget()
        grid = QGridLayout(self.new_update_widget)

        grid.addWidget(QLabel("Fabricante:"), 0, 0)
        self.manufacturer_cb = QComboBox()
        self.manufacturer_cb.addItem("Todas")
        manufacturers = queries.get_manufacturers(conn)
        self.manufacturer_cb.addItems(manufacturers)
        grid.addWidget(self.manufacturer_cb, 0, 1)
        self.manufacturer_cb.currentTextChanged.connect(self.update_model_list)

        grid.addWidget(QLabel("Modelo:"), 1, 0)
        self.model_list = QListWidget()
        grid.addWidget(self.model_list, 1, 1)

        grid.addWidget(QLabel("Versión:"), 2, 0)
        self.version_edit = QLineEdit()
        grid.addWidget(self.version_edit, 2, 1)

        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.add_device_update)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        grid.addLayout(button_layout, 3, 0, 1, 2)

        self.tab_layout = QTabWidget()
        self.tab_layout.addTab(self.new_update_widget, "Nueva actualización")
        self.tab_layout.addTab(self.table_widget, "Registro de actualizaciones")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_layout)
        self.setLayout(main_layout)

    def update_model_list(self):
        manufacturer_filter = self.manufacturer_cb.currentText()
        models = queries.get_models_by_manufacturer(self.conn, manufacturer_filter)

        self.model_list.blockSignals(True)
        self.model_list.clear()
        for model in models:
            item = QListWidgetItem(model)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.model_list.addItem(item)
        self.model_list.blockSignals(False)

    def add_device_update(self):
        manufacturer = self.manufacturer_cb.currentText()
        version = self.version_edit.text().strip()

        selected_models = []
        for i in range(self.model_list.count()):
            item = self.model_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_models.append(item.text())

        if not selected_models or not version:
            QMessageBox.warning(self, "Error", "Debe seleccionar al menos un modelo y escribir la versión.")
            return False

        try:
            added_any = False
            for model in selected_models:
                if queries.add_device_update(self.conn, manufacturer, model, "v" + version):
                    added_any = True

            if added_any:
                current_text = self.version_edit.text()
                if current_text:
                    self.version_edit.setText(f"{current_text},{version}")
                else:
                    self.version_edit.setText(version)

                self.model.removeRows(0, self.model.rowCount())
                updates = queries.get_latest_device_updates(self.conn)
                for row in updates:
                    items = [QStandardItem(str(field)) for field in row]
                    self.model.appendRow(items)

                self.version_edit.clear()
                for i in range(self.model_list.count()):
                    self.model_list.item(i).setCheckState(Qt.Unchecked)

                QMessageBox.information(self, "Éxito", "Actualización añadida correctamente.")
                return True
            else:
                QMessageBox.information(self, "Info", "La versión ya existe para los modelos seleccionados.")
                return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un problema: {e}")
            return False
