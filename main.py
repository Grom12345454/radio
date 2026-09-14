import sys
import os
import tkinter as tk
from ui.app_3d import RadioApp3D
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    root = tk.Tk()
    app = RadioApp3D(root)
    root.mainloop()


if __name__ == "__main__":
    main()