import tkinter as tk
from ui.app_3d import RadioApp3D


def main():
    root = tk.Tk()
    app = RadioApp3D(root)
    root.mainloop()


if __name__ == "__main__":
    main()