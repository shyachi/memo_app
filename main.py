import tkinter as tk
from ui import MemoApp

def main():
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
