import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import xml.etree.ElementTree as ET
from xml.dom import minidom
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

        # Treeviewの作成
        self.tree = ttk.Treeview(self.left_frame, columns=('date',), show='tree headings')
        self.tree.heading('date', text='日付')
        self.tree.column('date', width=100)
        
        # Treeviewのスクロールバー
        self.scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)

        # メモ項目の初期化
        self.memo_items = {}
        self.current_memo_id = None

        # 右側のフレーム（編集エリア用）
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # 編集エリアの上部フレーム
        self.edit_top_frame = ttk.Frame(self.right_frame)
        self.edit_top_frame.pack(fill='x', pady=(0, 5))

        # タイトル編集
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(self.edit_top_frame, textvariable=self.title_var)
        self.title_entry.pack(side='left', fill='x', expand=True)

        # 日付選択
        self.date_entry = DateEntry(self.edit_top_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, locale='ja_JP',
                                  date_pattern='yyyy/mm/dd')
        self.date_entry.pack(side='left', padx=5)

        # 削除ボタン
        self.delete_button = ttk.Button(self.edit_top_frame, text="削除", command=self.delete_current_memo)
        self.delete_button.pack(side='right', padx=5)

        # テキストエリアの作成
        self.text_area = tk.Text(self.right_frame, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill='both')

        # イベントの設定
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.title_var.trace_add('write', self.on_title_change)
        self.date_entry.bind('<<DateEntrySelected>>', self.on_date_change)
        self.text_area.bind('<<Modified>>', self.on_text_modified)

        # 初期メモの追加
        self.add_memo()

    def add_memo(self):
        # 新規メモの作成
        memo_id = str(len(self.memo_items))
        title = "新規メモ"
        date = datetime.now().strftime('%Y/%m/%d')
        
        # Treeviewに追加
        item = self.tree.insert('', 'end', memo_id, text=title, values=(date,))
        
        # メモデータの保存
        self.memo_items[memo_id] = {
            'title': title,
            'date': date,
            'content': ''
        }
        
        # 新規メモを選択
        self.tree.selection_set(item)
        self.tree.see(item)
        self.on_tree_select(None)

    def delete_current_memo(self):
        if len(self.memo_items) <= 1:
            messagebox.showwarning("警告", "最後のメモは削除できません。")
            return

        if self.current_memo_id:
            # 現在のメモを削除
            self.tree.delete(self.current_memo_id)
            del self.memo_items[self.current_memo_id]
            
            # 他のメモを選択
            remaining = self.tree.get_children()
            if remaining:
                self.tree.selection_set(remaining[0])
                self.tree.see(remaining[0])
                self.on_tree_select(None)
            else:
                self.add_memo()

    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        # 現在のメモIDを更新
        self.current_memo_id = selection[0]
        memo = self.memo_items[self.current_memo_id]
        
        # UI更新
        self.title_var.set(memo['title'])
        self.date_entry.set_date(datetime.strptime(memo['date'], '%Y/%m/%d').date())
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, memo['content'])
        self.text_area.edit_modified(False)

    def on_title_change(self, *args):
        if self.current_memo_id:
            title = self.title_var.get()
            self.memo_items[self.current_memo_id]['title'] = title
            self.tree.item(self.current_memo_id, text=title)

    def on_date_change(self, event):
        if self.current_memo_id:
            date = self.date_entry.get_date().strftime('%Y/%m/%d')
            self.memo_items[self.current_memo_id]['date'] = date
            self.tree.set(self.current_memo_id, 'date', date)

    def on_text_modified(self, event=None):
        if self.text_area.edit_modified() and self.current_memo_id:
            self.memo_items[self.current_memo_id]['content'] = self.text_area.get(1.0, tk.END)
            self.text_area.edit_modified(False)

    def save_file(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XMLファイル", "*.xml"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                # XML構造の作成
                root = ET.Element("memos")
                for memo_id, memo in self.memo_items.items():
                    memo_elem = ET.SubElement(root, "memo")
                    name = ET.SubElement(memo_elem, "name")
                    name.text = memo['title']
                    date = ET.SubElement(memo_elem, "date")
                    date.text = memo['date']
                    content = ET.SubElement(memo_elem, "content")
                    content.text = memo['content']

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
                for item_id in self.tree.get_children():
                    self.tree.delete(item_id)
                self.memo_items.clear()
                
                # メモデータの読み込み
                for i, memo in enumerate(root.findall('memo')):
                    memo_id = str(i)
                    title = memo.find('name').text or "新規メモ"
                    date_text = memo.find('date').text if memo.find('date') is not None else datetime.now().strftime('%Y/%m/%d')
                    content = memo.find('content').text or ""
                    
                    # Treeviewに追加
                    self.tree.insert('', 'end', memo_id, text=title, values=(date_text,))
                    
                    # メモデータの保存
                    self.memo_items[memo_id] = {
                        'title': title,
                        'date': date_text,
                        'content': content
                    }
                
                # メモが1つも読み込まれなかった場合は新規メモを作成
                if not self.memo_items:
                    self.add_memo()
                else:
                    # 最初のメモを選択
                    first_id = self.tree.get_children()[0]
                    self.tree.selection_set(first_id)
                    self.tree.see(first_id)
                    self.on_tree_select(None)
                
                messagebox.showinfo("読み込み完了", "ファイルを読み込みました。")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開く際にエラーが発生しました：{str(e)}")

def main():
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
