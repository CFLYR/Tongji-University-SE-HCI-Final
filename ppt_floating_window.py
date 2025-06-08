from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import sys

class PPTFloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(320, 180)
        self.setStyleSheet("background: rgba(255,255,255,0.95); border-radius: 12px; border: 1px solid #ccc;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 顶部按钮区
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始")
        self.btn_prev = QPushButton("上一页")
        self.btn_next = QPushButton("下一页")
        for btn in [self.btn_start, self.btn_prev, self.btn_next]:
            btn.setFixedHeight(32)
            btn.setStyleSheet("QPushButton { background: #165DFF; color: white; border-radius: 6px; font-weight: bold; padding: 0 12px; } QPushButton:hover { background: #466BB0; }")
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_prev)
        btn_layout.addWidget(self.btn_next)
        layout.addLayout(btn_layout)

        # 文稿展示区
        self.text_label = QLabel("文稿展示区")
        self.text_label.setStyleSheet("font-size: 15px; color: #222; background: #F5F5F5; border-radius: 6px; padding: 8px;")
        self.text_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumHeight(70)
        layout.addWidget(self.text_label)

        # 可选：底部拖动条或关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("QPushButton { background: none; color: #888; font-size: 18px; border: none; } QPushButton:hover { color: #D32F2F; }")
        close_btn.clicked.connect(self.close)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False
    def set_script_text(self, text):
        self.text_label.setText(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PPTFloatingWindow()
    win.show()
    sys.exit(app.exec()) 