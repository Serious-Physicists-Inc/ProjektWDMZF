stylesheet = """
QMainWindow, QWidget {
    background-color: #2b2d30;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 11pt;
}

QLabel {
    background-color: transparent;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #3c3f41;
    border-radius: 4px;
    background: #2b2d30;
}
QTabBar::tab {
    background: #3c3f41;
    color: #bbb;
    padding: 8px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #4e5254;
    color: white;
    font-weight: bold;
    border-bottom: 2px solid #00BCff;
}

/* Inputs */
QLineEdit {
    background-color: #1e1f22;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px;
    color: white;
    font-weight: bold;
}
QLineEdit:focus {
    border: 1px solid #00BCff;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* Buttons */
QPushButton {
    background-color: #36393d;
    border: 1px solid #555;
    border-radius: 5px;
    padding: 6px 12px;
    color: white;
}
QPushButton:hover {
    background-color: #4e5254;
}
QPushButton#PrimaryButton {
    background-color: #00BCff;
    border: none;
    color: black;
    font-weight: bold;
    font-size: 15px;
    padding: 10px;
}
QPushButton#PrimaryButton:hover {
    background-color: #33c9ff;
}
QPushButton#DestructiveButton {
    background-color: transparent;
    color: #ff6b6b;
    border: 1px solid #ff6b6b;
    font-weight: bold;
    font-size: 15px;
}
QPushButton#DestructiveButton:hover {
    background-color: #ff6b6b;
    color: white;
}

/* Cards */
QFrame#StateCard {
    background-color: #3c3f41;
    border-radius: 8px;
    border: 1px solid #4e5254;
}
"""

__all__ = ['stylesheet']