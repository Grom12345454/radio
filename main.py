import tkinter as tk
from ui.app import RadioApp

def main():
    root = tk.Tk()
    app = RadioApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()