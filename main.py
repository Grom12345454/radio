import tkinter as tk
from ui.app_3d import RadioApp3D
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualizer import Visualizer

def main():
    root = tk.Tk()
    app = RadioApp3D(root)
    root.mainloop()


if __name__ == "__main__":
    main()