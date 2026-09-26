"""
Upload Widget for uploading Excel files and syncing with PostgreSQL database.
Clean corporate interface without emojis.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt

from src.core.data_loader import DataLoader
from src.db.ingest import ingest_excel_to_db


class UploadWidget(QWidget):
    """Widget allowing lecturers to upload Excel data and preview database tables."""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_current_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Section
        header = QHBoxLayout()
        header_text = QVBoxLayout()
        title = QLabel("Quản lý & Tải Dữ liệu Sinh viên")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Tải file Excel dữ liệu sinh viên mới hoặc xem danh sách hiện tại trong PostgreSQL Database.")
        subtitle.setObjectName("sectionSubtitle")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text)
        header.addStretch()

        self.btn_upload = QPushButton("Upload File Excel Mới")
        self.btn_upload.setObjectName("primary-btn")
        self.btn_upload.clicked.connect(self.handle_upload)
        header.addWidget(self.btn_upload)

        layout.addLayout(header)

        # Status Label
        self.lbl_status = QLabel("Trạng thái Database: Sẵn sàng")
        self.lbl_status.setStyleSheet("color: #48cae4; font-weight: 600; font-size: 13px; margin-bottom: 6px;")
        layout.addWidget(self.lbl_status)

        # Table Preview
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def load_current_data(self):
        """Loads data from PostgreSQL database into table preview."""
        try:
            df = DataLoader.load_from_db()
            if df.empty:
                self.lbl_status.setText("Chưa có dữ liệu trong Database.")
                return

            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels(df.columns)

            for i in range(len(df)):  # Display all rows in database
                for j, col in enumerate(df.columns):
                    val = str(df.iloc[i, j])
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(i, j, item)

            self.lbl_status.setText(f"Trạng thái: Đã tải thành công {len(df):,} bản ghi sinh viên từ PostgreSQL Database.")
        except Exception as e:
            self.lbl_status.setText(f"Lỗi truy vấn Database: {str(e)}")

    def handle_upload(self):
        """Handles Excel file selection and database ingestion."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel Dữ liệu Sinh viên", "", "Excel Files (*.xlsx *.xls)"
        )

        if not file_path:
            return

        try:
            inserted = ingest_excel_to_db(Path(file_path))
            QMessageBox.information(
                self, "Thành công", f"Đã nạp thành công {inserted:,} bản ghi sinh viên vào Database!"
            )
            self.load_current_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Nạp Dữ liệu", f"Không thể nạp dữ liệu: {str(e)}")
