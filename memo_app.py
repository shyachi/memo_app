import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from tkcalendar import DateEntry
import locale

class MemoApp:
    def __init__(self, root):
        self.root = root
        self.current_file = None
        self.update_title()
        self.root.geometry("1000x600")

        # メニューバーの作成
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # ファイルメニュー
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="ファイル", menu=self.file_menu)

        # フィルターメニュー
        self.filter_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="フィルター", menu=self.filter_menu)
        self.filter_menu.add_command(label="タグでフィルター", command=self.show_tag_filter_dialog)
        self.file_menu.add_command(label="開く (Ctrl+O)", command=self.open_file, accelerator="Control-O")
        self.file_menu.add_command(label="上書き保存 (Ctrl+S)", command=self.save_file, accelerator="Control-S")
        self.file_menu.add_command(label="名前をつけて保存", command=self.save_file_as)
        self.file_menu.add_command(label="エクスポート", command=self.show_export_dialog)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="終了", command=self.root.quit)

        # キーボードショートカットの設定
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-O>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.save_file())

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
        self.tree = ttk.Treeview(self.left_frame, columns=('title', 'date', 'tags'), show='headings')
        self.tree_style = ttk.Style()
        self.tree_style.configure('Filtered.Treeview', background='#FFE6E6')
        self.is_filtered = False
        
        # タイトル列の設定
        self.tree.heading('title', text='タイトル', command=self.sort_by_title)
        self.tree.column('title', width=150)
        
        # 日付列の設定
        self.tree.heading('date', text='日付', command=self.sort_by_date)
        self.tree.column('date', width=100)

        # タグ列の設定
        self.tree.heading('tags', text='タグ')
        self.tree.column('tags', width=150)
        
        # ソート状態の初期化
        self.sort_reverse_date = False
        self.sort_reverse_title = False
        
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

        # タグ編集エリアの作成
        self.tags_frame = ttk.LabelFrame(self.right_frame, text="タグ", padding=5)
        self.tags_frame.pack(fill='x', pady=5)

        # タグ表示ラベル
        self.tags_label = ttk.Label(self.tags_frame, text="")
        self.tags_label.pack(side='left', fill='x', expand=True)

        # タグ編集フレーム
        self.tag_edit_frame = ttk.Frame(self.tags_frame)
        self.tag_edit_frame.pack(side='right')

        # タグ入力フィールド
        self.tag_var = tk.StringVar()
        self.tag_entry = ttk.Entry(self.tag_edit_frame, textvariable=self.tag_var, width=20)
        self.tag_entry.pack(side='left', padx=5)

        # タグ追加ボタン
        self.add_tag_button = ttk.Button(self.tag_edit_frame, text="追加", command=self.add_tag)
        self.add_tag_button.pack(side='left', padx=2)

        # タグ削除ボタン
        self.remove_tag_button = ttk.Button(self.tag_edit_frame, text="削除", command=self.remove_tag)
        self.remove_tag_button.pack(side='left', padx=2)

        # イベントの設定
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.title_var.trace_add('write', self.on_title_change)
        self.date_entry.bind('<<DateEntrySelected>>', self.on_date_change)
        self.text_area.bind('<<Modified>>', self.on_text_modified)

        # 初期メモの追加
        self.add_memo()

    def add_tag(self):
        if not self.current_memo_id:
            return
        
        tag = self.tag_var.get().strip()
        if tag:
            memo = self.memo_items[self.current_memo_id]
            if 'tags' not in memo:
                memo['tags'] = set()
            memo['tags'].add(tag)
            self.update_tags_display()
            self.tag_var.set("")  # 入力フィールドをクリア

    def remove_tag(self):
        if not self.current_memo_id:
            return
        
        tag = self.tag_var.get().strip()
        if tag:
            memo = self.memo_items[self.current_memo_id]
            if 'tags' in memo and tag in memo['tags']:
                memo['tags'].remove(tag)
                self.update_tags_display()
            self.tag_var.set("")  # 入力フィールドをクリア

    def update_tags_display(self):
        if not self.current_memo_id:
            return
        
        memo = self.memo_items[self.current_memo_id]
        tags = memo.get('tags', set())
        tags_str = ', '.join(sorted(tags))
        
        # タグラベルの更新
        self.tags_label.config(text=tags_str)
        
        # Treeviewのタグ列を更新
        self.tree.set(self.current_memo_id, 'tags', tags_str)

    def sort_by_title(self):
        items = [(self.tree.set(item, 'title'), item) for item in self.tree.get_children('')]
        locale.setlocale(locale.LC_ALL, '')
        items.sort(key=lambda x: locale.strxfrm(x[0]), reverse=self.sort_reverse_title)
        self.sort_reverse_title = not self.sort_reverse_title
        for index, (title, item) in enumerate(items):
            self.tree.move(item, '', index)

    def sort_by_date(self):
        items = [(self.tree.set(item, 'date'), item) for item in self.tree.get_children('')]
        items.sort(reverse=self.sort_reverse_date)
        self.sort_reverse_date = not self.sort_reverse_date
        for index, (date, item) in enumerate(items):
            self.tree.move(item, '', index)

    def add_memo(self):
        memo_id = str(len(self.memo_items))
        title = "新規メモ"
        date = datetime.now().strftime('%Y/%m/%d')
        
        item = self.tree.insert('', 'end', memo_id, values=(title, date, ""))
        
        self.memo_items[memo_id] = {
            'title': title,
            'date': date,
            'content': '',
            'tags': set()
        }
        
        self.tree.selection_set(item)
        self.tree.see(item)
        self.on_tree_select(None)

    def delete_current_memo(self):
        if len(self.memo_items) <= 1:
            messagebox.showwarning("警告", "最後のメモは削除できません。")
            return

        if self.current_memo_id:
            self.tree.delete(self.current_memo_id)
            del self.memo_items[self.current_memo_id]
            
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
        
        self.current_memo_id = selection[0]
        memo = self.memo_items[self.current_memo_id]
        
        self.title_var.set(memo['title'])
        self.date_entry.set_date(datetime.strptime(memo['date'], '%Y/%m/%d').date())
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, memo['content'])
        self.text_area.edit_modified(False)
        
        self.update_tags_display()

    def on_title_change(self, *args):
        if self.current_memo_id:
            title = self.title_var.get()
            self.memo_items[self.current_memo_id]['title'] = title
            self.tree.set(self.current_memo_id, 'title', title)

    def on_date_change(self, event):
        if self.current_memo_id:
            date = self.date_entry.get_date().strftime('%Y/%m/%d')
            self.memo_items[self.current_memo_id]['date'] = date
            self.tree.set(self.current_memo_id, 'date', date)

    def on_text_modified(self, event=None):
        if self.text_area.edit_modified() and self.current_memo_id:
            self.memo_items[self.current_memo_id]['content'] = self.text_area.get(1.0, tk.END)
            self.text_area.edit_modified(False)

    def update_title(self):
        base_title = "メモ帳"
        if self.current_file:
            self.root.title(f"{base_title} - {self.current_file}")
        else:
            self.root.title(base_title)

    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XMLファイル", "*.xml"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                self.save_to_file(file_path)
                self.current_file = file_path
                self.update_title()
        except Exception as e:
            messagebox.showerror("エラー", f"保存中にエラーが発生しました：{str(e)}")

    def save_to_file(self, file_path):
        try:
            root = ET.Element("memos")
            for memo_id, memo in self.memo_items.items():
                memo_elem = ET.SubElement(root, "memo")
                name = ET.SubElement(memo_elem, "name")
                name.text = memo['title']
                date = ET.SubElement(memo_elem, "date")
                date.text = memo['date']
                content = ET.SubElement(memo_elem, "content")
                content.text = memo['content']
                tags = ET.SubElement(memo_elem, "tags")
                tags.text = ','.join(sorted(memo.get('tags', set())))

            xml_str = minidom.parseString(ET.tostring(root, 'utf-8')).toprettyxml(indent="    ")
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(xml_str)
            
            messagebox.showinfo("保存完了", "ファイルを保存しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"保存中にエラーが発生しました：{str(e)}")
            raise

    def show_tag_filter_dialog(self):
        TagFilterDialog(self.root, self)

    def get_all_tags(self):
        all_tags = set()
        for memo in self.memo_items.values():
            all_tags.update(memo.get('tags', set()))
        return sorted(all_tags)

    def update_buttons_state(self):
        # フィルター状態に応じてボタンの状態を設定
        state = 'disabled' if self.is_filtered else 'normal'
        self.add_button.configure(state=state)
        self.add_tag_button.configure(state=state)
        self.remove_tag_button.configure(state=state)
        self.tag_entry.configure(state=state)

    def apply_tag_filter(self, selected_tags):
        if not selected_tags:
            # フィルター解除
            self.tree.configure(style='')
            self.is_filtered = False
            
            # すべてのメモを再表示
            self.tree.delete(*self.tree.get_children())  # 現在の表示をクリア
            for memo_id, memo in self.memo_items.items():
                title = memo['title']
                date = memo['date']
                tags_str = ', '.join(sorted(memo.get('tags', set())))
                self.tree.insert('', 'end', memo_id, values=(title, date, tags_str))
        else:
            # フィルター適用
            self.tree.configure(style='Filtered.Treeview')
            self.is_filtered = True

            # 現在の表示をクリア
            self.tree.delete(*self.tree.get_children())

            # 条件に合うメモのみを表示し、最初の該当メモのIDを記録
            first_filtered_id = None
            current_memo_filtered = False

            for memo_id, memo in self.memo_items.items():
                memo_tags = memo.get('tags', set())
                if any(tag in memo_tags for tag in selected_tags):
                    title = memo['title']
                    date = memo['date']
                    tags_str = ', '.join(sorted(memo_tags))
                    self.tree.insert('', 'end', memo_id, values=(title, date, tags_str))
                    
                    if first_filtered_id is None:
                        first_filtered_id = memo_id
                    if memo_id == self.current_memo_id:
                        current_memo_filtered = True

            # 選択状態の更新
            if first_filtered_id:
                if not current_memo_filtered:
                    # 現在選択中のメモがフィルターで除外された場合、最初の該当メモを選択
                    self.tree.selection_set(first_filtered_id)
                    self.tree.see(first_filtered_id)
                    self.on_tree_select(None)
                else:
                    # 現在選択中のメモが表示されている場合、その選択を維持
                    self.tree.selection_set(self.current_memo_id)
                    self.tree.see(self.current_memo_id)

        # ボタンの状態を更新
        self.update_buttons_state()

    def show_export_dialog(self):
        ExportDialog(self.root, self)

    def export_memos(self, selected_only=False):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as file:
                    if selected_only and self.current_memo_id:
                        memo = self.memo_items[self.current_memo_id]
                        file.write(f"タイトル: {memo['title']}\n")
                        file.write(f"日付: {memo['date']}\n")
                        file.write(f"タグ: {', '.join(sorted(memo.get('tags', set())))}\n")
                        file.write(f"内容:\n{memo['content']}\n")
                    else:
                        for memo_id in self.tree.get_children():
                            memo = self.memo_items[memo_id]
                            file.write(f"タイトル: {memo['title']}\n")
                            file.write(f"日付: {memo['date']}\n")
                            file.write(f"タグ: {', '.join(sorted(memo.get('tags', set())))}\n")
                            file.write(f"内容:\n{memo['content']}\n")
                            file.write("-" * 50 + "\n")
                
                messagebox.showinfo("エクスポート完了", "メモをエクスポートしました。")
        except Exception as e:
            messagebox.showerror("エラー", f"エクスポート中にエラーが発生しました：{str(e)}")

    def open_file(self):
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("XMLファイル", "*.xml"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                self.current_file = file_path
                self.update_title()
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                for item_id in self.tree.get_children():
                    self.tree.delete(item_id)
                self.memo_items.clear()
                
                for i, memo in enumerate(root.findall('memo')):
                    memo_id = str(i)
                    title = memo.find('name').text or "新規メモ"
                    date_text = memo.find('date').text if memo.find('date') is not None else datetime.now().strftime('%Y/%m/%d')
                    content = memo.find('content').text or ""
                    tags_text = memo.find('tags').text if memo.find('tags') is not None else ""
                    tags = set(filter(None, tags_text.split(','))) if tags_text else set()
                    
                    self.tree.insert('', 'end', memo_id, values=(title, date_text, ', '.join(sorted(tags))))
                    
                    self.memo_items[memo_id] = {
                        'title': title,
                        'date': date_text,
                        'content': content,
                        'tags': tags
                    }
                
                if not self.memo_items:
                    self.add_memo()
                else:
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

class ExportDialog:
    def __init__(self, parent, app):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("エクスポート設定")
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.export_frame = ttk.LabelFrame(self.dialog, text="エクスポート範囲", padding=10)
        self.export_frame.pack(fill='x', padx=10, pady=5)
        
        self.export_var = tk.StringVar(value="all")
        ttk.Radiobutton(self.export_frame, text="すべてのメモ", 
                       variable=self.export_var, value="all").pack(anchor='w')
        ttk.Radiobutton(self.export_frame, text="選択中のメモのみ", 
                       variable=self.export_var, value="selected").pack(anchor='w')
        
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="キャンセル", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        ttk.Button(button_frame, text="エクスポート", 
                  command=lambda: self.export(app)).pack(side='right')

    def export(self, app):
        selected_only = self.export_var.get() == "selected"
        self.dialog.destroy()
        app.export_memos(selected_only)

class TagFilterDialog:
    def __init__(self, parent, app):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("タグでフィルター")
        self.dialog.geometry("300x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # タグ選択フレーム
        self.tag_frame = ttk.LabelFrame(self.dialog, text="フィルターするタグを選択", padding=10)
        self.tag_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # タグ選択用のListbox（複数選択可能）
        self.tag_listbox = tk.Listbox(self.tag_frame, selectmode=tk.MULTIPLE)
        self.tag_listbox.pack(fill='both', expand=True)

        # 利用可能なタグを取得してListboxに追加
        for tag in app.get_all_tags():
            self.tag_listbox.insert(tk.END, tag)

        # ボタンフレーム
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)

        # フィルター解除ボタン
        ttk.Button(button_frame, text="フィルター解除", 
                  command=lambda: self.apply_filter(app, None)).pack(side='left', padx=5)

        # キャンセルボタン
        ttk.Button(button_frame, text="キャンセル", 
                  command=self.dialog.destroy).pack(side='right', padx=5)

        # 実行ボタン
        ttk.Button(button_frame, text="実行", 
                  command=lambda: self.apply_filter(app)).pack(side='right')

    def apply_filter(self, app, selected_tags=None):
        if selected_tags is None and self.tag_listbox.curselection():
            # 選択されたタグを取得
            selected_tags = [self.tag_listbox.get(i) for i in self.tag_listbox.curselection()]
        
        app.apply_tag_filter(selected_tags)
        self.dialog.destroy()

if __name__ == "__main__":
    main()
