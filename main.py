import tkinter as tk
from ui import MemoApp

def main():
    """
    メモアプリケーションのメインエントリーポイント
    Tkinterウィンドウを作成し、アプリケーションを起動する
    """
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
