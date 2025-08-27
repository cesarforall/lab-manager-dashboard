import sys
import sqlite3
import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QListWidget, QListWidgetItem, QGridLayout, QGroupBox, QScrollArea,
    QSizePolicy, QCheckBox, QFileDialog, QSplitter
)
from PyQt6.QtCore import Qt
from functools import partial
from lab_manager.data.database import get_connection, init_db
from lab_manager.data import queries

from lab_manager.utils import export

WIDGET_WIDTH = 150
WIDGET_HEIGHT = 180
FIXED_WIDTH = 180
FIXED_HEIGHT = 180
MAX_COLS = 10
MAX_ROWS = 6
MAX_SCALE = 2  # factor máximo de expansión


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lab Manager - Dashboard")
        self.resize(1000, 700)

        init_db()
        self.conn = get_connection()

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        filters_container = QVBoxLayout()
        filter_widget = QWidget()
        filter_widget.setLayout(filters_container)
        main_layout.addWidget(filter_widget)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        filters_container.addLayout(filter_layout)

        label = QLabel("Filtrar por marca:")
        filter_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop)

        self.manufacturer_cb = QComboBox()
        self.manufacturer_cb.addItem("Todas")
        manufacturers = queries.get_manufacturers(self.conn)
        self.manufacturer_cb.addItems(manufacturers)
        self.manufacturer_cb.setFixedWidth(150)
        filter_layout.addWidget(self.manufacturer_cb, alignment=Qt.AlignmentFlag.AlignTop)
        self.manufacturer_cb.currentTextChanged.connect(self.update_model_list)

        label = QLabel("Filtrar por modelo:")
        filter_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignTop)

        self.model_list = QListWidget()
        self.model_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.model_list.setMaximumHeight(80)
        self.model_list.setMaximumWidth(180)
        self.model_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        filter_layout.addWidget(self.model_list, alignment=Qt.AlignmentFlag.AlignTop)
        self.model_list.itemChanged.connect(self.update_dashboard)

        self.pending_cb = QCheckBox("Solo pendientes")
        filter_layout.addWidget(self.pending_cb, alignment=Qt.AlignmentFlag.AlignTop)
        self.pending_cb.stateChanged.connect(self.update_dashboard)

        filter_layout.addStretch()

        tech_view_layout = QHBoxLayout()
        filters_container.addLayout(tech_view_layout)

        self.toggle_sidebar_left_btn = QPushButton("Técnicos")
        self.toggle_sidebar_left_btn.setCheckable(True)
        self.toggle_sidebar_left_btn.clicked.connect(lambda checked: self.left_sidebar_scroll.setVisible(checked))
        tech_view_layout.addWidget(self.toggle_sidebar_left_btn)

        tech_view_layout.addStretch()

        self.tech_count_label = QLabel("Técnicos disponibles: 0")
        self.tech_count_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        tech_view_layout.addWidget(self.tech_count_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.export_btn = QPushButton("Excel")
        tech_view_layout.addWidget(self.export_btn)
        self.export_btn.clicked.connect(self.export_current_dashboard)

        self.grid_btn = QPushButton("Cuadrícula")
        self.list_btn = QPushButton("Lista")
        tech_view_layout.addWidget(self.grid_btn)
        tech_view_layout.addWidget(self.list_btn)
        self.view_mode = "grid"
        self.grid_btn.clicked.connect(lambda: self.set_view_mode("grid"))
        self.list_btn.clicked.connect(lambda: self.set_view_mode("list"))

        self.toggle_sidebar_btn = QPushButton("Actualizaciones")
        self.toggle_sidebar_btn.setCheckable(True)
        self.toggle_sidebar_btn.clicked.connect(lambda checked: self.sidebar_scroll.setVisible(checked))
        tech_view_layout.addWidget(self.toggle_sidebar_btn)

        self.left_sidebar = QWidget()
        self.left_sidebar_layout = QVBoxLayout()
        self.left_sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.left_sidebar_layout.setSpacing(0)
        self.left_sidebar.setLayout(self.left_sidebar_layout)

        self.technician_list = QListWidget()
        self.left_sidebar_layout.addWidget(self.technician_list)

        self.left_sidebar_scroll = QScrollArea()
        self.left_sidebar_scroll.setWidgetResizable(True)
        self.left_sidebar_scroll.setWidget(self.left_sidebar)
        self.left_sidebar_scroll.setVisible(False)

        self.dashboard_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_widget.setLayout(self.grid_layout)

        ws_scroll = QScrollArea()
        ws_scroll.setWidgetResizable(True)
        ws_scroll.setWidget(self.dashboard_widget)

        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(0)
        self.sidebar.setLayout(self.sidebar_layout)

        self.latest_updates_list = QListWidget()
        self.sidebar_layout.addWidget(self.latest_updates_list)

        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setWidget(self.sidebar)
        self.sidebar_scroll.setVisible(False)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.left_sidebar_scroll.setMinimumWidth(100)
        self.left_sidebar_scroll.setMaximumWidth(400)
        splitter.addWidget(self.left_sidebar_scroll)
        splitter.addWidget(ws_scroll)
        self.sidebar_scroll.setMinimumWidth(100)
        self.sidebar_scroll.setMaximumWidth(400)
        splitter.addWidget(self.sidebar_scroll)
        splitter.setSizes([200, 600, 200])
        main_layout.addWidget(splitter)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

        self.update_model_list()
        self.update_technician_list()
    
    def set_view_mode(self, mode):
            self.view_mode = mode
            self.update_dashboard()

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

        self.update_dashboard()

    def update_dashboard(self):
        # Limpiar grid
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        manufacturer_filter = self.manufacturer_cb.currentText()
        selected_models = [
            self.model_list.item(i).text()
            for i in range(self.model_list.count())
            if self.model_list.item(i).checkState() == Qt.CheckState.Checked
        ]
        filter_active = (manufacturer_filter != "Todas") or (len(selected_models) > 0)

        # Total de técnicos
        total_techs = queries.get_total_technicians(self.conn)

        ws_rows = queries.get_workstations_with_assignments(self.conn)
        num_techs = 0
        row_counter = 0

        for ws_id, tech_id, ws_name, tech_name, pos_x, pos_y, pc_serial in ws_rows:
            pending_only = self.pending_cb.isChecked()
            if tech_id is None and (filter_active or pending_only):
                continue

            pc_label = f" ({pc_serial})" if pc_serial else ""
            group = QGroupBox(f"{ws_name}{pc_label}")
            group.setFixedSize(FIXED_WIDTH, FIXED_HEIGHT)

            inner_widget = QWidget()
            v_layout = QVBoxLayout()
            v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(0)
            inner_widget.setLayout(v_layout)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(inner_widget)
            scroll_area.setContentsMargins(0, 0, 0, 0)
            scroll_area.setStyleSheet("QScrollArea { border-top: none; }")

            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(0)
            group_layout.addWidget(scroll_area)
            group.setLayout(group_layout)

            # Si no hay técnico
            if tech_id is None:
                no_technician = QLabel("Sin técnico")
                no_technician.setContentsMargins(2, 0, 0, 0)
                v_layout.addWidget(no_technician)
            else:
                # Filtrado de dispositivos del técnico
                tech_data = queries.get_technician_devices(self.conn, tech_id)
                tech_manufacturers = [b for b, m in tech_data]
                tech_models = [m for b, m in tech_data]

                if filter_active:
                    if manufacturer_filter != "Todas" and manufacturer_filter not in tech_manufacturers:
                        continue
                    if selected_models and not any(m in selected_models for m in tech_models):
                        continue

                # Filtrado solo pendientes
                if self.pending_cb.isChecked():
                    pending_count = queries.get_pending_updates_count(
                        self.conn, tech_id, manufacturer_filter, selected_models
                    )
                    if pending_count == 0:
                        continue

                num_techs += 1

                # Nombre del técnico
                technician = QLabel(f"Técnico: {tech_name}")
                technician.setContentsMargins(2, 0, 0, 0)
                v_layout.addWidget(technician)

                # Actualizaciones del técnico
                updates = queries.get_latest_updates_for_technician(self.conn, tech_id)
                for manufacturer, model, version, confirmed, update_id in updates:
                    if selected_models and model not in selected_models:
                        continue
                    if manufacturer_filter != "Todas" and manufacturer != manufacturer_filter:
                        continue

                    row_layout = QHBoxLayout()
                    row_layout.setContentsMargins(1, 0, 0, 0)
                    row_layout.setSpacing(5)

                    if confirmed:
                        btn = QPushButton("✅")
                        btn.setFixedSize(20, 20)
                        btn.setToolTip(f"{manufacturer} {model}: {version} (Actualizado)")
                        btn.setEnabled(False)
                        btn.setStyleSheet("""
                            QPushButton {
                                background: transparent;
                                border: none;
                            }
                        """)
                        row_layout.addWidget(btn)
                    else:
                        btn = QPushButton("⏳")
                        btn.setToolTip(f"Marcar {manufacturer} {model}: {version} como actualizado")
                        btn.setFixedSize(20, 20)
                        btn.clicked.connect(partial(self.mark_update, tech_id, update_id))
                        row_layout.addWidget(btn)

                    text = QLabel(f"{manufacturer} {model}: {version}")
                    row_layout.addWidget(text)
                    row_layout.addStretch()

                    row_widget = QWidget()
                    row_widget.setLayout(row_layout)
                    v_layout.addWidget(row_widget)

            if self.view_mode == "grid":
                self.grid_layout.addWidget(group, pos_y, pos_x)
            else:
                self.grid_layout.addWidget(group, row_counter, 0)
                row_counter += 1

        # Actualizar contador
        self.tech_count_label.setText(f"Técnicos: {num_techs} / {total_techs}")

        # Rellenar celdas vacías solo en vista grid
        if self.view_mode == "grid":
            for row in range(MAX_ROWS):
                for col in range(MAX_COLS):
                    if not self.grid_layout.itemAtPosition(row, col):
                        placeholder = QWidget()
                        placeholder.setFixedSize(FIXED_WIDTH, FIXED_HEIGHT)
                        self.grid_layout.addWidget(placeholder, row, col)

        self.update_latest_updates()

    def update_latest_updates(self):
        self.latest_updates_list.clear()
        updates = queries.get_latest_device_updates(self.conn, limit=20)
        for manufacturer, model, version, created_at in updates:
            item_text = f"{created_at[:16]} - {manufacturer} {model}: {version}"
            self.latest_updates_list.addItem(item_text)

    def update_technician_list(self):
        self.technician_list.clear()
        technicians = queries.get_all_technicians(self.conn)
        for tech_id, name, created_at in technicians:
            self.technician_list.addItem(name)

    def mark_update(self, technician_id, update_id):
        queries.mark_update_as_confirmed(self.conn, technician_id, update_id)
        self.update_dashboard()

    def export_current_dashboard(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"dashboard_{timestamp}.xlsx"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Excel",
            default_name,
            "Archivos Excel (*.xlsx)"
        )
        if not path:
            return

        data = []
        manufacturer_filter = self.manufacturer_cb.currentText()
        selected_models = [
            self.model_list.item(i).text()
            for i in range(self.model_list.count())
            if self.model_list.item(i).checkState() == Qt.CheckState.Checked
        ]
        pending_only = self.pending_cb.isChecked()

        ws_rows = queries.get_workstations_with_assignments(self.conn)
        for ws_id, tech_id, ws_name, tech_name, pos_x, pos_y, pc_serial in ws_rows:
            if tech_id is None:
                continue

            updates = queries.get_latest_updates_for_technician(self.conn, tech_id)
            for manufacturer, model, version, confirmed, update_id in updates:
                if manufacturer_filter != "Todas" and manufacturer != manufacturer_filter:
                    continue
                if selected_models and model not in selected_models:
                    continue
                if pending_only and confirmed:
                    continue

                data.append({
                    "Workstation": ws_name,
                    "Técnico": tech_name,
                    "PC": pc_serial,
                    "Fabricante": manufacturer,
                    "Modelo": model,
                    "Versión": version,
                    "Actualizado": bool(confirmed)
                })

        export_path = export.export_to_excel(data, path)
        if export_path:
            print(f"Exportado a {export_path}")
