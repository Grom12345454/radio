import sys
import os

# Сначала добавляем корень проекта в пути поиска
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk

# Импортируем правильный класс RadioApp3D
from ui.app import RadioApp3D

def main():
    root = tk.Tk()
    app = RadioApp3D(root)
    root.mainloop()

if __name__ == "__main__":
    main()