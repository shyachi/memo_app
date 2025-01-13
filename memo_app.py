import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import xml.etree.ElementTree as ET
from xml.dom import minidom
from ttkwidgets.frames import ScrolledFrame
from datetime import datetime
from tkcalendar import DateEntry

class MemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("メモ帳")
        self.root.geometry("1000x600")

        # メニューバーの作成
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # ファイルメニュー
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="ファイル", menu=self.file_menu)
        self.file_menu.add_command(label="開く", command=self.open_file)
        self.file_menu.add_command(label="保存", command=self.save_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="終了", command=self.root.quit)

        # メインフレームの作成
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')

        # 左側のフレーム（メモリスト用）
        self.left_frame = ttk.Frame(self.main_frame, width=300)
        self.left_frame.pack(side='left', fill='y', padx=5, pady=5)

        # メモ追加ボタン
        self.add_button = ttk.Button(self.left_frame, text="新規メモ追加", command=self.add_memo)
        self.add_button.pack(fill='x', pady=(0, 5))

        # スクロール可能なフレームの作成
        self.scrolled_frame = ScrolledFrame(self.left_frame, width=280)
        self.scrolled_frame.pack(fill='both', expand=True)

        # メモリストの作成
        self.memo_list_frame = self.scrolled_frame.interior
        
        # メモ項目の初期化
        self.memo_items = []
        self.current_memo_index = None

        # 右側のフレーム（テキストエリア用）
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # テキストエリアの作成
        self.text_area = tk.Text(self.right_frame, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill='both')

        # 初期メモの追加
        self.add_memo()

        # テキスト変更イベントの設定
        self.text_area.bind('<<Modified>>', self.on_text_modified)

    def create_memo_item(self, name="新規メモ"):
        item_frame = ttk.Frame(self.memo_list_frame)
        item_frame.pack(fill='x', pady=2)
        
        # メモ項目のメインフレーム
        main_item_frame = ttk.Frame(item_frame)
        main_item_frame.pack(fill='x', pady=2)
        
        # 名前入力フィールド
        name_var = tk.StringVar(value=name)
        name_entry = ttk.Entry(main_item_frame, textvariable=name_var)
        name_entry.pack(side='left', fill='x', expand=True)
        
        # 日時選択
        date_var = tk.StringVar()
        date_entry = DateEntry(main_item_frame, width=12, background='darkblue',
                             foreground='white', borderwidth=2, locale='ja_JP',
                             date_pattern='yyyy/mm/dd')
        date_entry.pack(side='left', padx=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_item_frame)
        button_frame.pack(side='right')
        
        # 選択ボタン
        select_button = ttk.Button(
            button_frame,
            text="選択",
            width=6
        )
        select_button.pack(side='left', padx=2)
        
        # 削除ボタン
        delete_button = ttk.Button(
            button_frame,
            text="削除",
            width=6
        )
        delete_button.pack(side='left', padx=2)
        
        memo_item = {
            'frame': item_frame,
            'name_var': name_var,
            'date_entry': date_entry,
            'content': '',
            'entry': name_entry,
            'select_button': select_button,
            'delete_button': delete_button
        }
        
        # ボタンのコマンドを設定
        index = len(self.memo_items)
        select_button.configure(command=lambda idx=index: self.select_memo(idx))
        delete_button.configure(command=lambda idx=index: self.delete_memo(idx))
        
        self.memo_items.append(memo_item)
        return memo_item

    def add_memo(self):
        memo_item = self.create_memo_item()
        if self.current_memo_index is None:
            self.select_memo(len(self.memo_items) - 1)

    def delete_memo(self, index):
        if len(self.memo_items) <= 1:
            messagebox.showwarning("警告", "最後のメモは削除できません。")
            return

        # メモアイテムの削除
        memo_item = self.memo_items.pop(index)
        memo_item['frame'].destroy()

        # インデックスの更新
        if self.current_memo_index == index:
            # 削除されたメモが選択中だった場合
            new_index = min(index, len(self.memo_items) - 1)
            self.current_memo_index = None
            self.select_memo(new_index)
        elif self.current_memo_index > index:
            # 削除されたメモが現在選択中のメモより前にあった場合
            self.current_memo_index -= 1

        # 残りのメモの削除ボタンのコマンドを更新
        for i, item in enumerate(self.memo_items):
            item['select_button'].configure(command=lambda idx=i: self.select_memo(idx))
            item['delete_button'].configure(command=lambda idx=i: self.delete_memo(idx))

    def on_text_modified(self, event=None):
        if self.text_area.edit_modified() and self.current_memo_index is not None:
            # 現在のテキストを保存
            self.memo_items[self.current_memo_index]['content'] = self.text_area.get(1.0, tk.END)
            self.text_area.edit_modified(False)

    def select_memo(self, index):
        if self.current_memo_index is not None:
            # 現在のテキストを保存
            self.memo_items[self.current_memo_index]['content'] = self.text_area.get(1.0, tk.END)
            # 前のボタンを有効化
            self.memo_items[self.current_memo_index]['select_button'].state(['!disabled'])
        
        # 新しいメモを選択
        self.current_memo_index = index
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, self.memo_items[index]['content'])
        
        # 選択されたメモのボタンを無効化
        self.memo_items[index]['select_button'].state(['disabled'])

    def save_file(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XMLファイル", "*.xml"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                # 現在のテキストを保存
                if self.current_memo_index is not None:
                    self.memo_items[self.current_memo_index]['content'] = self.text_area.get(1.0, tk.END)

                # XML構造の作成
                root = ET.Element("memos")
                for item in self.memo_items:
                    memo = ET.SubElement(root, "memo")
                    name = ET.SubElement(memo, "name")
                    name.text = item['name_var'].get()
                    date = ET.SubElement(memo, "date")
                    date.text = item['date_entry'].get_date().strftime('%Y/%m/%d')
                    content = ET.SubElement(memo, "content")
                    content.text = item['content']

                # XMLの整形
                xml_str = minidom.parseString(ET.tostring(root, 'utf-8')).toprettyxml(indent="    ")
                
                # ファイルに保存
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(xml_str)
                
                messagebox.showinfo("保存完了", "ファイルを保存しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"保存中にエラーが発生しました：{str(e)}")

    def open_file(self):
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("XMLファイル", "*.xml"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # 既存のメモをクリア
                for item in self.memo_items:
                    item['frame'].destroy()
                self.memo_items.clear()
                
                # メモデータの読み込み
                for memo in root.findall('memo'):
                    name = memo.find('name').text or "新規メモ"
                    date_text = memo.find('date').text if memo.find('date') is not None else ""
                    content = memo.find('content').text or ""
                    
                    memo_item = self.create_memo_item(name)
                    if date_text:
                        try:
                            date = datetime.strptime(date_text, '%Y/%m/%d').date()
                            memo_item['date_entry'].set_date(date)
                        except ValueError:
                            pass
                    memo_item['content'] = content
                
                # メモが1つも読み込まれなかった場合は新規メモを作成
                if not self.memo_items:
                    self.add_memo()
                
                # 最初のメモを選択
                self.current_memo_index = None
                self.select_memo(0)
                
                messagebox.showinfo("読み込み完了", "ファイルを読み込みました。")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開く際にエラーが発生しました：{str(e)}")

def main():
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
