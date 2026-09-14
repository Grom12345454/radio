import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk

from ui.app_3d import RadioApp

def main():
    root = tk.Tk()
    app = RadioApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()