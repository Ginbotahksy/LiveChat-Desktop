from PyQt6.QtCore import QTimer, QCoreApplication
import sys
app = QCoreApplication(sys.argv)
t = QTimer()
try:
    t.start("2000")
    print("Success")
except Exception as e:
    print("Error:", repr(e))
