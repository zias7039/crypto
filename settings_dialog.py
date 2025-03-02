# settings_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QGroupBox, QFormLayout, QLineEdit, QSlider, QFontComboBox,
    QVBoxLayout, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class SettingsDialog(QDialog):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.initUI()

        self.symbol_input.textChanged.connect(self.update_overlay_preview)
        self.font_slider.valueChanged.connect(self.update_overlay_preview)
        self.width_slider.valueChanged.connect(self.update_overlay_preview)
        self.height_slider.valueChanged.connect(self.update_overlay_preview)
        self.opacity_slider.valueChanged.connect(self.update_overlay_preview)
        self.font_combo.currentFontChanged.connect(self.update_overlay_preview)

    def initUI(self):
        self.setWindowTitle("설정")
        self.setFixedSize(400, 320)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(8)

        general_group = QGroupBox("일반 설정")
        general_layout = QFormLayout()
        general_layout.setSpacing(8)
        self.symbol_input = QLineEdit()
        self.symbol_input.setText(", ".join(self.overlay.symbols))
        general_layout.addRow("티커 입력:", self.symbol_input)
        general_group.setLayout(general_layout)

        appearance_group = QGroupBox("디자인 설정")
        appearance_layout = QFormLayout()
        appearance_layout.setSpacing(8)

        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.overlay.font_name))
        appearance_layout.addRow("폰트 선택:", self.font_combo)

        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(8, 30)
        self.font_slider.setValue(self.overlay.font_size)
        appearance_layout.addRow("폰트 크기:", self.font_slider)

        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setRange(100, 500)
        self.width_slider.setValue(self.overlay.window_width)
        appearance_layout.addRow("창 너비:", self.width_slider)

        self.height_slider = QSlider(Qt.Horizontal)
        self.height_slider.setRange(40, 500)
        self.height_slider.setValue(self.overlay.window_height)
        appearance_layout.addRow("창 높이:", self.height_slider)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.overlay.opacity_level * 100))
        appearance_layout.addRow("투명도:", self.opacity_slider)

        appearance_group.setLayout(appearance_layout)

        button_layout = QVBoxLayout()
        close_button = QPushButton("닫기")
        button_layout.addWidget(close_button)

        main_layout.addWidget(general_group)
        main_layout.addWidget(appearance_group)
        main_layout.addLayout(button_layout)

        close_button.clicked.connect(self.save_and_close)

        self.setStyleSheet("""  /* 원하는 다크 스타일시트 */  """)

    def update_overlay_preview(self):
        syms = self.symbol_input.text()
        self.overlay.symbols = [s.strip().upper() for s in syms.split(",") if s.strip()]
        self.overlay.font_size = self.font_slider.value()
        self.overlay.window_width = self.width_slider.value()
        self.overlay.window_height = self.height_slider.value()
        self.overlay.opacity_level = self.opacity_slider.value() / 100.0
        self.overlay.font_name = self.font_combo.currentFont().family()
        self.overlay.apply_settings()

    def save_and_close(self):
        self.update_overlay_preview()
        self.overlay.save_settings()
        self.hide()

    def closeEvent(self, event):
        self.save_and_close()
        event.ignore()
