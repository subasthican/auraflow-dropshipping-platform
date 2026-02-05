import time
from PySide6.QtCore import QThread, Signal

class BackgroundWorker(QThread):
    task_completed = Signal(str)

    def __init__(self, interval=3600):
        super().__init__()
        self.interval = interval
        self.running = True

    def run(self):
        while self.running:
            try:
                # Pulse Logic
                self.task_completed.emit("Background sync completed successfully.")
            except Exception as e:
                self.task_completed.emit(f"Error in background task: {str(e)}")
            
            # Responsive Sleep: check self.running every 1 second
            for _ in range(self.interval):
                if not self.running:
                    return
                time.sleep(1)

    def stop(self):
        self.running = False
