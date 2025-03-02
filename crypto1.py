import sys
import requests
import json
import datetime

from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QPushButton,
    QSlider, QDialog, QGroupBox, QGraphicsDropShadowEffect,
    QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation
from PyQt5.QtGui import QFont, QColor


class SettingsDialog(QDialog):
    def __init__(self, overlay):
        super().__init__(None)
        self.overlay = overlay
        self.initUI()

    def initUI(self):
        self.setWindowTitle("설정")
        self.setFixedSize(380, 300)

        # 전체 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # [1] 일반 설정 (티커, 업데이트 주기)
        general_group = QGroupBox("일반 설정")
        general_layout = QFormLayout()
        general_layout.setSpacing(8)

        # 티커(symbol) 입력
        self.symbol_input = QLineEdit(self)
        self.symbol_input.setText(self.overlay.current_symbol)
        self.symbol_input.textChanged.connect(self.overlay.update_symbol)
        general_layout.addRow("티커 입력:", self.symbol_input)

        # 업데이트 주기(초 단위)
        self.refresh_slider = QSlider(Qt.Horizontal)
        self.refresh_slider.setMinimum(1)
        self.refresh_slider.setMaximum(30)
        self.refresh_slider.setValue(self.overlay.refresh_interval)
        self.refresh_slider.valueChanged.connect(self.overlay.update_refresh_interval)
        general_layout.addRow("업데이트 주기(초):", self.refresh_slider)

        general_group.setLayout(general_layout)

        # [2] 디자인 설정 (폰트, 창 크기)
        appearance_group = QGroupBox("디자인 설정")
        appearance_layout = QVBoxLayout()
        appearance_layout.setSpacing(8)

        # 폰트 크기 조절
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setMinimum(8)
        self.font_slider.setMaximum(30)
        self.font_slider.setValue(self.overlay.font_size)
        self.font_slider.valueChanged.connect(self.overlay.update_font_size)

        # 창 너비 조절
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setMinimum(100)
        self.width_slider.setMaximum(500)
        self.width_slider.setValue(self.overlay.window_width)
        self.width_slider.valueChanged.connect(self.overlay.update_window_width)

        # 창 높이 조절
        self.height_slider = QSlider(Qt.Horizontal)
        self.height_slider.setMinimum(40)
        self.height_slider.setMaximum(500)
        self.height_slider.setValue(self.overlay.window_height)
        self.height_slider.valueChanged.connect(self.overlay.update_window_height)

        appearance_layout.addWidget(QLabel("폰트 크기 조절"))
        appearance_layout.addWidget(self.font_slider)
        appearance_layout.addWidget(QLabel("창 너비 조절"))
        appearance_layout.addWidget(self.width_slider)
        appearance_layout.addWidget(QLabel("창 높이 조절"))
        appearance_layout.addWidget(self.height_slider)
        appearance_group.setLayout(appearance_layout)

        # 닫기 버튼
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.hide)

        # 메인 레이아웃에 그룹박스들 + 닫기 버튼 배치
        main_layout.addWidget(general_group)
        main_layout.addWidget(appearance_group)
        main_layout.addWidget(close_button, alignment=Qt.AlignRight)

        self.setLayout(main_layout)

        # 다이얼로그 스타일시트
        self.setStyleSheet("""
            QDialog {
                background-color: #2B2B2B;
            }
            QGroupBox {
                color: #FFFFFF;
                border: 1px solid #5C5C5C;
                border-radius: 5px;
                margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                top: 2px;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #5C5C5C;
                border-radius: 4px;
                padding: 4px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #3C3C3C;
            }
            QSlider::handle:horizontal {
                background: #CCCCCC;
                border: 1px solid #5C5C5C;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #3C3F41;
                color: #FFFFFF;
                border: 1px solid #5C5C5C;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #505357;
            }
        """)

    def closeEvent(self, event):
        """
        X 버튼을 눌러 닫아도 실제로 닫지 않고 숨기기만 함
        """
        self.hide()
        event.ignore()


class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.load_settings()

        # 업데이트 주기(초) 기본값
        self.refresh_interval = getattr(self, "refresh_interval", 2)
        self.morning_price = None  # 당일 9시 가격 저장

        self.initUI()
        self.dragging = False
        self.offset = QPoint()
        self.price_animation = QPropertyAnimation(self, b"windowOpacity")
        self.price_animation.setDuration(300)
        self.settings_dialog = None

    def initUI(self):
        # 투명한 창 + 항상 위에 표시 + 테두리 없음
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setAlignment(Qt.AlignCenter)

        # 가격 표시 라벨
        self.label = QLabel("Loading...", self)
        self.label.setFont(QFont("Segoe UI", self.font_size, QFont.Bold))
        self.label.setStyleSheet("""
            color: #ffffff;
            background-color: rgba(40, 40, 40, 180);
            border: 1px solid rgba(255, 255, 255, 50);
            border-radius: 8px;
            padding: 10px;
        """)
        self.label.setFixedSize(self.window_width, self.window_height)
        self.label.setAlignment(Qt.AlignCenter)

        # 그림자 효과
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.label.setGraphicsEffect(shadow)

        # ────────────────────────────────────────────────────────
        # 라벨을 마우스 이벤트에서 투명 처리 (드래그 문제 해결)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        # ────────────────────────────────────────────────────────

        layout.addWidget(self.label)
        self.setLayout(layout)

        self.resize(self.window_width, self.window_height)
        self.move(self.window_x, self.window_y)
        self.setWindowOpacity(self.opacity_level)

        # 업데이트 주기 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_price)
        self.timer.start(self.refresh_interval * 1000)

    # ESC 키를 누르면 오버레이 종료
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.pos()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.open_settings()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.save_settings()
            event.accept()

    def open_settings(self):
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()

    def save_settings(self):
        settings = {
            "symbol": self.current_symbol,
            "opacity": self.opacity_level,
            "window_x": self.x(),
            "window_y": self.y(),
            "font_size": self.font_size,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "refresh_interval": self.refresh_interval
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.current_symbol = settings.get("symbol", "ETHUSDT")
                self.opacity_level = settings.get("opacity", 1.0)
                self.window_x = settings.get("window_x", 1600)
                self.window_y = settings.get("window_y", 50)
                self.font_size = settings.get("font_size", 12)
                self.window_width = settings.get("window_width", 300)
                self.window_height = settings.get("window_height", 40)
                self.refresh_interval = settings.get("refresh_interval", 2)
        except FileNotFoundError:
            self.current_symbol = "ETHUSDT"
            self.opacity_level = 1.0
            self.window_x = 1600
            self.window_y = 50
            self.font_size = 12
            self.window_width = 300
            self.window_height = 40
            self.refresh_interval = 2

    def fetch_morning_price(self):
        try:
            today = datetime.date.today()
            nine_am = datetime.datetime(today.year, today.month, today.day, 9, 0, 0)
            timestamp = int(nine_am.timestamp() * 1000)
            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": self.current_symbol,
                "interval": "1h",
                "startTime": timestamp,
                "endTime": timestamp + 60 * 60 * 1000,
                "limit": 1
            }
            response = requests.get(url, params=params)
            data = response.json()
            if data and len(data) > 0:
                self.morning_price = float(data[0][1])  # 9시 시가
        except Exception:
            self.morning_price = None

    def update_price(self):
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            response = requests.get(url, params={"symbol": self.current_symbol})
            data = response.json()
            current_price = float(data.get("price", 0))

            now_hour = datetime.datetime.now().hour
            if now_hour >= 9 and self.morning_price is None:
                self.fetch_morning_price()

            diff = 0.0
            diff_percent = 0.0
            if self.morning_price is not None:
                diff = current_price - self.morning_price
                # 0이 아닌 경우에만 퍼센트 계산
                if self.morning_price != 0:
                    diff_percent = (diff / self.morning_price) * 100

            # 변동폭 색상 표시: 양수(녹색), 음수(빨간색), 0(흰색)
            if diff > 0:
                diff_color = "#00FF00"  # 녹색
            elif diff < 0:
                diff_color = "#FF4C4C"  # 빨간색
            else:
                diff_color = "#FFFFFF"  # 흰색

            # 표시 포맷: 티커명 가격 변동폭(%)
            text = (f"{self.current_symbol} {current_price:.2f} "
                    f"<span style='color:{diff_color}'>{diff_percent:.2f}%</span>")
            self.label.setText(text)
        except Exception:
            self.label.setText("Error fetching price")

    # 설정창과 연동되는 메서드들
    def update_symbol(self, new_symbol):
        self.current_symbol = new_symbol.upper().strip()
        self.morning_price = None  # 심볼 바뀌면 9시 가격 재조회
        self.save_settings()

    def update_refresh_interval(self, value):
        self.refresh_interval = value
        self.timer.setInterval(self.refresh_interval * 1000)
        self.save_settings()

    def update_font_size(self, value):
        self.font_size = value
        self.label.setFont(QFont("Segoe UI", self.font_size, QFont.Bold))
        self.label.setFixedSize(self.window_width, self.window_height)
        self.save_settings()

    def update_window_width(self, value):
        self.window_width = value
        self.label.setFixedSize(self.window_width, self.window_height)
        self.resize(self.window_width, self.window_height)
        self.save_settings()

    def update_window_height(self, value):
        self.window_height = value
        self.label.setFixedSize(self.window_width, self.window_height)
        self.resize(self.window_width, self.window_height)
        self.save_settings()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = Overlay()
    overlay.show()
    sys.exit(app.exec_())
