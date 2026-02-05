"""
Simple toast notification system using QTimer and QLabel.
Non-intrusive feedback for user actions without blocking dialogs.
"""
from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PySide6.QtGui import QFont, QColor


class Toast:
    """Lightweight toast notification that auto-dismisses after a duration."""
    
    _active_toast = None  # Class variable to track active toast
    
    def __init__(self, message: str, duration: int = 3000, parent=None, toast_type: str = "info"):
        """
        Args:
            message: Text to display.
            duration: How long to show in milliseconds (default 3s).
            parent: Parent widget (used for positioning).
            toast_type: "success", "info", "error", or "warning".
        """
        self.message = message
        self.duration = duration
        self.parent = parent
        self.toast_type = toast_type
        self.label = None
        self.timer = None
        
    def show(self):
        """Display the toast notification."""
        # Dismiss any active toast first
        if Toast._active_toast is not None:
            Toast._active_toast._dismiss()
        Toast._active_toast = self
        
        # Create label
        self.label = QLabel(self.message)
        self.label.setObjectName("Toast")
        self.label.setWordWrap(False)
        
        # Styling based on type
        colors = {
            "success": ("#10b981", "#ffffff"),  # green
            "error": ("#ef4444", "#ffffff"),     # red
            "warning": ("#f59e0b", "#ffffff"),   # amber
            "info": ("#3b82f6", "#ffffff"),      # blue
        }
        bg_color, text_color = colors.get(self.toast_type, colors["info"])
        
        self.label.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            border: none;
        """)
        
        # Position at bottom-center of parent or screen
        if self.parent:
            parent_geo = self.parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - 300) // 2
            y = parent_geo.y() + parent_geo.height() - 80
        else:
            # Fallback: center bottom of available screen space
            x = 50
            y = 50
        
        self.label.move(x, y)
        self.label.setFixedWidth(300)
        self.label.show()
        
        # Auto-dismiss timer
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._dismiss)
        self.timer.start(self.duration)
    
    def _dismiss(self):
        """Hide and clean up the toast."""
        if self.label:
            self.label.hide()
            self.label.deleteLater()
            self.label = None
        if self.timer:
            self.timer.stop()
            self.timer = None
        if Toast._active_toast is self:
            Toast._active_toast = None


def show_toast(message: str, duration: int = 3000, parent=None, toast_type: str = "info"):
    """Convenience function to show a toast notification."""
    toast = Toast(message, duration, parent, toast_type)
    toast.show()
