"""
Upload Widget for uploading Excel files and syncing with PostgreSQL database.
Clean corporate interface without emojis.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

import pandas as pd
from src.core.data_loader import DataLoader
from src.data.ingestion import ingest_file, parse_excel
from src.data.validator import DataValidator
from src.db.connection import SessionLocal, Base, engine
from src.core.exceptions import DataValidationError, IngestionError, SchemaError


class UploadWidget(QWidget):
    """Widget allowing lecturers to upload Excel data and preview database tables."""

    data_reloaded = pyqtSignal()

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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def load_current_data(self):
        """Loads data from PostgreSQL database into table preview."""
        try:
            df = DataLoader.load_from_db()
            source_name = "PostgreSQL Database"
            if df.empty:
                df = DataLoader.load_data()
                source_name = "Dữ liệu Offline (Excel)"

            if df.empty:
                self.lbl_status.setText("Chưa có dữ liệu sinh viên.")
                return

            preview_limit = min(len(df), 200)
            self.table.setRowCount(preview_limit)
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels(df.columns)

            for i in range(preview_limit):
                for j, col in enumerate(df.columns):
                    val = df.iloc[i, j]
                    if pd.isna(val) or val is None or str(val).strip().lower() in ["none", "nan", "<na>", ""]:
                        item = QTableWidgetItem("Chưa có dữ liệu")
                        item.setForeground(Qt.GlobalColor.red)
                    else:
                        item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(i, j, item)

            if len(df) > preview_limit:
                self.lbl_status.setText(f"Trạng thái: Đã tải {len(df):,} bản ghi ({source_name}) — hiển thị {preview_limit} bản ghi xem trước.")
            else:
                self.lbl_status.setText(f"Trạng thái: Đã tải thành công {len(df):,} bản ghi sinh viên ({source_name}).")
        except Exception as e:
            self.lbl_status.setText(f"Lỗi tải dữ liệu: {str(e)}")

    def handle_upload(self):
        """Handles Excel file selection and transactional ingestion pipeline (DB-002, DB-003)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Excel Dữ liệu Sinh viên", "", "Excel Files (*.xlsx *.xls)"
        )

        if not file_path:
            return

        try:
            path_obj = Path(file_path)
            # Step 1: Pre-validation of file
            df_preview = parse_excel(path_obj)
            val_result = DataValidator.validate(df_preview)

            if not val_result.is_valid:
                QMessageBox.critical(
                    self, "Kiểm tra Dữ liệu Thất bại",
                    f"Dữ liệu không hợp lệ ({val_result.error_count} lỗi). Cơ sở dữ liệu không bị thay đổi.\n\n"
                    f"{val_result.summary()}"
                )
                return

            # Step 2: Ingest into Database transactionally
            session = SessionLocal()
            try:
                Base.metadata.create_all(bind=engine)
                ingest_res = ingest_file(path_obj, session)
                inserted = ingest_res.rows_inserted
                warn_text = ""
                if ingest_res.warnings:
                    warn_text = f"\n\nLưu ý cảnh báo ({len(ingest_res.warnings)}): " + "; ".join(ingest_res.warnings[:3])

                QMessageBox.information(
                    self, "Thành công",
                    f"Đã kiểm tra và nạp thành công {inserted:,} bản ghi sinh viên vào Database!{warn_text}"
                )
            except Exception as dbe:
                # If database is offline, fallback to updating local offline view
                session.rollback()
                DataLoader.clear_cache()
                QMessageBox.warning(
                    self, "Database Offline",
                    f"Dữ liệu Excel hợp lệ ({len(df_preview):,} dòng) nhưng không kết nối được PostgreSQL:\n{dbe}\n"
                    "Hệ thống sẽ chạy ở chế độ Dữ liệu Offline (Excel)."
                )
            finally:
                session.close()

            DataLoader.clear_cache()
            self.load_current_data()
            self.data_reloaded.emit()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi Nạp Dữ liệu", f"Không thể xử lý file: {str(e)}")
