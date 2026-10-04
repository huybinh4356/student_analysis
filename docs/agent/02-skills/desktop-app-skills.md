# SKILLS — Desktop App

## S-APP-01: Xây dựng PyQt6 UI
**Khả năng:**
- Main window + sidebar + tabs.
- Menu bar + toolbar + status bar.
- Stylesheet (QSS).
- Threading cho task nặng.

**Cấu trúc:**
```python
# main_window.py
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
    
    def _init_ui(self):
        # Sidebar + Tabs
        pass
## S-APP-02: Kết nối UI với core logic
Khả năng:

Signal/slot trong PyQt.

Worker thread cho training.

Progress bar.

Error handling.

Code mẫu:

python
from PyQt6.QtCore import QThread, pyqtSignal

class AnalysisWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, data, config):
        super().__init__()
        self.data = data
        self.config = config
    
    def run(self):
        try:
            self.progress.emit(10)
            # Xử lý dữ liệu
            self.progress.emit(50)
            # Train model
            self.progress.emit(100)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
## S-APP-03: Đóng gói .exe
Khả năng:

PyInstaller.

Xử lý dependencies.

Tạo icon, splash screen.

Inno Setup installer.

Command:

bash
pyinstaller --name="StudentAnalysisApp" \
            --windowed \
            --onefile \
            --icon=assets/logo.ico \
            --add-data="ui/styles.qss;ui" \
            --add-data="assets;assets" \
            --add-data="data;data" \
            main.py