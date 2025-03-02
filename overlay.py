# overlay.py
import json
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor, QKeySequence
from PyQt5.QtWidgets import QShortcut

from price_fetcher import PriceFetcherThread
from settings_dialog import SettingsDialog

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_config_path():
    # 중복 방지를 위해, 혹은 import from main... etc.
    # 여기에 복붙 or 다른 방법
    import os
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, ".myCryptoOverlay")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "settings.json")


class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.symbols = ["ETHUSDT"]
        self.font_name = "Segoe UI"
        self.opacity_level = 1.0
        self.window_x = 1600
        self.window_y = 50
        self.font_size = 12
        self.window_width = 300
        self.window_height = 40
        self.refresh_interval = 2

        self.load_settings()
        self.initUI()
        self.settings_dialog = None

        QShortcut(QKeySequence("F2"), self, self.open_settings)
        QShortcut(QKeySequence("F5"), self, self.update_price)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_price)
        self.timer.start(self.refresh_interval * 1000)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("로딩 중...", self)
        self.label.setFont(QFont(self.font_name, self.font_size, QFont.Bold))
        self.label.setStyleSheet("""
            color: #FFF;
            background-color: rgba(40,40,40,200);
            border: 1px solid rgba(80,80,80,120);
            border-radius: 10px;
            padding: 10px;
        """)
        self.label.setFixedSize(self.window_width, self.window_height)
        self.label.setAlignment(Qt.AlignCenter)

        # 그림자 (원치 않으면 주석 처리)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(3,3)
        shadow.setColor(QColor(0,0,0,180))
        self.label.setGraphicsEffect(shadow)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        layout.addWidget(self.label)
        self.resize(self.window_width, self.window_height)
        self.move(self.window_x, self.window_y)
        self.setWindowOpacity(self.opacity_level)

    def apply_settings(self):
        self.label.setFont(QFont(self.font_name, self.font_size, QFont.Bold))
        self.label.setFixedSize(self.window_width, self.window_height)
        self.resize(self.window_width, self.window_height)
        self.setWindowOpacity(self.opacity_level)

    def save_settings(self):
        cfg = {
            "symbols": self.symbols,
            "font_name": self.font_name,
            "opacity": self.opacity_level,
            "window_x": self.x(),
            "window_y": self.y(),
            "font_size": self.font_size,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "refresh_interval": self.refresh_interval
        }
        try:
            with open(get_config_path(), "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            logging.info("설정 저장 완료")
        except Exception as e:
            logging.error(f"설정 저장 실패: {e}")

    def load_settings(self):
        import os
        try:
            with open(get_config_path(), "r", encoding="utf-8") as f:
                s = json.load(f)
        except:
            s = {}
        self.symbols = s.get("symbols", ["ETHUSDT"])
        self.font_name = s.get("font_name", "Segoe UI")
        self.opacity_level = s.get("opacity", 1.0)
        self.window_x = s.get("window_x", 1600)
        self.window_y = s.get("window_y", 50)
        self.font_size = s.get("font_size", 12)
        self.window_width = s.get("window_width", 300)
        self.window_height = s.get("window_height", 40)
        self.refresh_interval = s.get("refresh_interval", 2)

    def update_price(self):
        self.fetcher = PriceFetcherThread(self.symbols)
        self.fetcher.result_ready.connect(self.update_price_slot)
        self.fetcher.start()

    def update_price_slot(self, results):
        lines = []
        for symbol, (binance_price, morning_diff, kimchi) in results.items():
            if binance_price is None:
                lines.append(f"{symbol}: N/A")
            else:
                price_str = f"{binance_price:,.2f}"
                if morning_diff is not None:
                    if morning_diff > 0:
                        diff_str = f"<span style='color:#4CAF50;'>▲ {morning_diff:.2f}%</span>"
                    elif morning_diff < 0:
                        diff_str = f"<span style='color:#F44336;'>▼ {-morning_diff:.2f}%</span>"
                    else:
                        diff_str = f"<span style='color:#FFF;'>0.00%</span>"
                else:
                    diff_str = "N/A"

                if kimchi is not None:
                    kimchi_str = f"<span style='color:#FFA500;'>{kimchi:.2f}%</span>"
                else:
                    kimchi_str = "N/A"

                line = (f"{symbol} &nbsp;&nbsp;&nbsp; {price_str} &nbsp;&nbsp;&nbsp;"
                        f"{diff_str} &nbsp;&nbsp;&nbsp; {kimchi_str}")
                lines.append(line)
        self.label.setText("<br>".join(lines))

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120
        new_opacity = self.opacity_level + (delta * 0.05)
        new_opacity = max(0.1, min(new_opacity, 1.0))
        self.opacity_level = new_opacity
        self.setWindowOpacity(self.opacity_level)
        self.save_settings()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.pos()
            self.setWindowOpacity(self.opacity_level * 0.8)
            event.accept()
        elif event.button() == Qt.RightButton:
            self.open_settings()
            event.accept()

    def mouseMoveEvent(self, event):
        if getattr(self, "dragging", False) and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setWindowOpacity(self.opacity_level)
            self.save_settings()
            event.accept()

    def open_settings(self):
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()  # or QApplication.quit()
        else:
            super().keyPressEvent(event)
