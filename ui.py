import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import locale
from logic import MemoManager, Memo

class MemoApp:
    def __init__(self, root):
        self.root = root
        self.memo_manager = MemoManager()
        self.current_memo_id = None
        self.is_tag_filtered = False
        self.is_date_filtered = False
        
        self._setup_window()
        self._create_menu()
        self._create_main_frame()
        self._setup_shortcuts()
        
        # 初期メモの追加
        self.add_memo()

    def _setup_window(self):
        self.root.geometry("1000x600")
        self.update_title()

    def update_title(self):
        base_title = "メモ帳"
        if self.memo_manager.current_file:
            self.root.title(f"{base_title} - {self.memo_manager.current_file}")
        else:
            self.root.title(base_title)

    def _create_menu(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # ファイルメニュー
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="ファイル", menu=self.file_menu)
        self.file_menu.add_command(label="開く (Ctrl+O)", command=self.open_file, accelerator="Control-O")
        self.file_menu.add_command(label="インポート", command=self.import_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="上書き保存 (Ctrl+S)", command=self.save_file, accelerator="Control-S")
        self.file_menu.add_command(label="名前をつけて保存", command=self.save_file_as)
        self.file_menu.add_command(label="エクスポート", command=self.show_export_dialog)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="終了", command=self.root.quit)

        # フィルターメニュー
        self.filter_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="フィルター", menu=self.filter_menu)
        self.filter_menu.add_command(label="タグでフィルター", command=self.show_tag_filter_dialog)
        self.filter_menu.add_command(label="日付でフィルター", command=self.show_date_filter_dialog)
        self.filter_menu.add_separator()
        self.filter_menu.add_command(label="すべてのフィルターを解除", command=self.clear_all_filters)

        # 検索メニュー
        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="検索", menu=self.search_menu)
        self.search_menu.add_command(label="メモを検索", command=self.show_search_dialog)

    def update_filter_menu(self):
        """フィルターメニューの表示を更新"""
        tag_label = "タグでフィルター（実行中）" if self.is_tag_filtered else "タグでフィルター"
        date_label = "日付でフィルター（実行中）" if self.is_date_filtered else "日付でフィルター"
        self.filter_menu.entryconfig(0, label=tag_label)
        self.filter_menu.entryconfig(1, label=date_label)

    def clear_all_filters(self):
        """すべてのフィルターを解除"""
        if self.is_tag_filtered or self.is_date_filtered:
            self.is_tag_filtered = False
            self.is_date_filtered = False
            self.refresh_memo_list()
            self.update_filter_menu()
            self.update_buttons_state()

    def refresh_memo_list(self):
        """メモリストを更新"""
        # 現在の表示をクリア
        self.tree.delete(*self.tree.get_children())

        # メモをフィルタリング
        filtered_ids = set(self.memo_manager.memos.keys())

        if self.is_tag_filtered and hasattr(self, 'current_tag_filter'):
            filtered_ids &= {memo_id for memo_id, memo in self.memo_manager.memos.items()
                           if any(tag in memo.tags for tag in self.current_tag_filter)}

        if self.is_date_filtered and hasattr(self, 'current_date_range'):
            start_date, end_date = self.current_date_range
            date_filtered_ids = self.memo_manager.filter_by_date(start_date, end_date)
            filtered_ids &= set(date_filtered_ids)

        # フィルター結果を表示
        first_filtered_id = None
        current_memo_filtered = False

        for memo_id in filtered_ids:
            memo = self.memo_manager.memos[memo_id]
            self.tree.insert('', 'end', memo_id, 
                           values=(memo.title, memo.date, ', '.join(sorted(memo.tags))))
            
            if first_filtered_id is None:
                first_filtered_id = memo_id
            if memo_id == self.current_memo_id:
                current_memo_filtered = True

        # 選択状態の更新
        if first_filtered_id:
            if not current_memo_filtered:
                self.tree.selection_set(first_filtered_id)
                self.tree.see(first_filtered_id)
                self.on_tree_select(None)
            else:
                self.tree.selection_set(self.current_memo_id)
                self.tree.see(self.current_memo_id)

        # スタイルの更新
        style = 'Filtered.Treeview' if self.is_tag_filtered or self.is_date_filtered else ''
        self.tree.configure(style=style)

    def _setup_shortcuts(self):
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-O>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.save_file())

    def _create_main_frame(self):
        # メインフレーム
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')

        # 左側のフレーム（メモリスト）
        self._create_left_frame()
        
        # 右側のフレーム（編集エリア）
        self._create_right_frame()

    def _create_left_frame(self):
        self.left_frame = ttk.Frame(self.main_frame, width=300)
        self.left_frame.pack(side='left', fill='y', padx=5, pady=5)

        # メモ追加ボタン
        self.add_button = ttk.Button(self.left_frame, text="新規メモ追加", command=self.add_memo)
        self.add_button.pack(fill='x', pady=(0, 5))

        # Treeviewの作成
        self._create_tree_view()

    def _create_tree_view(self):
        self.tree = ttk.Treeview(self.left_frame, columns=('title', 'date', 'tags'), show='headings')
        self.tree_style = ttk.Style()
        self.tree_style.configure('Filtered.Treeview', background='#FFE6E6')
        
        # 列の設定
        self.tree.heading('title', text='タイトル', command=self.sort_by_title)
        self.tree.column('title', width=150)
        self.tree.heading('date', text='日付', command=self.sort_by_date)
        self.tree.column('date', width=100)
        self.tree.heading('tags', text='タグ')
        self.tree.column('tags', width=150)
        
        # ソート状態の初期化
        self.sort_reverse_date = False
        self.sort_reverse_title = False
        
        # スクロールバー
        self.scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        
        # 選択イベントの設定
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def _create_right_frame(self):
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # 上部フレーム
        self._create_edit_top_frame()

        # テキストエリア
        self.text_area = tk.Text(self.right_frame, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill='both')
        self.text_area.bind('<<Modified>>', self.on_text_modified)

        # タグ編集エリア
        self._create_tags_frame()

    def _create_edit_top_frame(self):
        self.edit_top_frame = ttk.Frame(self.right_frame)
        self.edit_top_frame.pack(fill='x', pady=(0, 5))

        # タイトル編集
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(self.edit_top_frame, textvariable=self.title_var)
        self.title_entry.pack(side='left', fill='x', expand=True)
        self.title_var.trace_add('write', self.on_title_change)

        # 日付選択
        self.date_entry = DateEntry(self.edit_top_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, locale='ja_JP',
                                  date_pattern='yyyy/mm/dd')
        self.date_entry.pack(side='left', padx=5)
        self.date_entry.bind('<<DateEntrySelected>>', self.on_date_change)

        # 削除ボタン
        self.delete_button = ttk.Button(self.edit_top_frame, text="削除", command=self.delete_current_memo)
        self.delete_button.pack(side='right', padx=5)

    def _create_tags_frame(self):
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

        # タグ操作ボタン
        self.add_tag_button = ttk.Button(self.tag_edit_frame, text="追加", command=self.add_tag)
        self.add_tag_button.pack(side='left', padx=2)
        self.remove_tag_button = ttk.Button(self.tag_edit_frame, text="削除", command=self.remove_tag)
        self.remove_tag_button.pack(side='left', padx=2)

    # イベントハンドラー
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        self.current_memo_id = selection[0]
        memo = self.memo_manager.memos[self.current_memo_id]
        
        self.title_var.set(memo.title)
        self.date_entry.set_date(datetime.strptime(memo.date, '%Y/%m/%d').date())
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, memo.content)
        self.text_area.edit_modified(False)
        
        self.update_tags_display()

    def on_title_change(self, *args):
        if self.current_memo_id:
            title = self.title_var.get()
            self.memo_manager.memos[self.current_memo_id].title = title
            self.tree.set(self.current_memo_id, 'title', title)

    def on_date_change(self, event):
        if self.current_memo_id:
            date = self.date_entry.get_date().strftime('%Y/%m/%d')
            self.memo_manager.memos[self.current_memo_id].date = date
            self.tree.set(self.current_memo_id, 'date', date)

    def on_text_modified(self, event=None):
        if self.text_area.edit_modified() and self.current_memo_id:
            self.memo_manager.memos[self.current_memo_id].content = self.text_area.get(1.0, tk.END)
            self.text_area.edit_modified(False)

    # メモ操作
    def add_memo(self):
        memo_id = self.memo_manager.add_memo()
        memo = self.memo_manager.memos[memo_id]
        
        self.tree.insert('', 'end', memo_id, values=(memo.title, memo.date, ""))
        self.tree.selection_set(memo_id)
        self.tree.see(memo_id)
        self.on_tree_select(None)

    def delete_current_memo(self):
        if len(self.memo_manager.memos) <= 1:
            messagebox.showwarning("警告", "最後のメモは削除できません。")
            return

        if self.current_memo_id:
            self.memo_manager.delete_memo(self.current_memo_id)
            self.tree.delete(self.current_memo_id)
            
            remaining = self.tree.get_children()
            if remaining:
                self.tree.selection_set(remaining[0])
                self.tree.see(remaining[0])
                self.on_tree_select(None)
            else:
                self.add_memo()

    # タグ操作
    def add_tag(self):
        if not self.current_memo_id:
            return

        tag = self.tag_var.get().strip()
        if tag:
            memo = self.memo_manager.memos[self.current_memo_id]
            memo.tags.add(tag)
            self.update_tags_display()
            self.tag_var.set("")
        else:
            TagSelectionDialog(self.root, self, "追加するタグを選択", self.add_selected_tags)

    def add_selected_tags(self, selected_tags):
        if not selected_tags or not self.current_memo_id:
            return
        
        memo = self.memo_manager.memos[self.current_memo_id]
        memo.tags.update(selected_tags)
        self.update_tags_display()

    def remove_tag(self):
        if not self.current_memo_id:
            return

        tag = self.tag_var.get().strip()
        if tag:
            memo = self.memo_manager.memos[self.current_memo_id]
            if tag in memo.tags:
                memo.tags.remove(tag)
                self.update_tags_display()
            self.tag_var.set("")
        else:
            TagSelectionDialog(self.root, self, "削除するタグを選択", self.remove_selected_tags)

    def remove_selected_tags(self, selected_tags):
        if not selected_tags or not self.current_memo_id:
            return
        
        memo = self.memo_manager.memos[self.current_memo_id]
        memo.tags -= set(selected_tags)
        self.update_tags_display()

    def update_tags_display(self):
        if not self.current_memo_id:
            return
        
        memo = self.memo_manager.memos[self.current_memo_id]
        tags_str = ', '.join(sorted(memo.tags))
        
        self.tags_label.config(text=tags_str)
        self.tree.set(self.current_memo_id, 'tags', tags_str)

    # ファイル操作
    def save_file(self):
        if self.memo_manager.current_file:
            try:
                self.memo_manager.save_to_file(self.memo_manager.current_file)
                messagebox.showinfo("保存完了", "ファイルを保存しました。")
            except Exception as e:
                messagebox.showerror("エラー", f"保存中にエラーが発生しました：{str(e)}")
        else:
            self.save_file_as()

    def save_file_as(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XMLファイル", "*.xml"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                self.memo_manager.save_to_file(file_path)
                self.update_title()
                messagebox.showinfo("保存完了", "ファイルを保存しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"保存中にエラーが発生しました：{str(e)}")

    def open_file(self):
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("XMLファイル", "*.xml"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                self.memo_manager.load_from_file(file_path)
                self.update_title()
                
                # Treeviewの更新
                for item_id in self.tree.get_children():
                    self.tree.delete(item_id)
                
                for memo_id, memo in self.memo_manager.memos.items():
                    self.tree.insert('', 'end', memo_id, 
                                   values=(memo.title, memo.date, ', '.join(sorted(memo.tags))))
                
                if not self.memo_manager.memos:
                    self.add_memo()
                else:
                    first_id = self.tree.get_children()[0]
                    self.tree.selection_set(first_id)
                    self.tree.see(first_id)
                    self.on_tree_select(None)
                
                messagebox.showinfo("読み込み完了", "ファイルを読み込みました。")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルを開く際にエラーが発生しました：{str(e)}")

    # ソート機能
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

    # フィルター機能
    def show_tag_filter_dialog(self):
        TagFilterDialog(self.root, self)

    def show_date_filter_dialog(self):
        DateFilterDialog(self.root, self)

    def show_search_dialog(self):
        """検索ダイアログを表示"""
        SearchDialog(self.root, self)

    def apply_date_filter(self, start_date: str, end_date: str):
        if not start_date or not end_date:
            self.is_date_filtered = False
            if hasattr(self, 'current_date_range'):
                delattr(self, 'current_date_range')
        else:
            self.is_date_filtered = True
            self.current_date_range = (start_date, end_date)

        self.refresh_memo_list()
        self.update_filter_menu()
        self.update_buttons_state()

    def apply_tag_filter(self, selected_tags):
        if not selected_tags:
            self.is_tag_filtered = False
            if hasattr(self, 'current_tag_filter'):
                delattr(self, 'current_tag_filter')
        else:
            self.is_tag_filtered = True
            self.current_tag_filter = selected_tags

        self.refresh_memo_list()
        self.update_filter_menu()
        self.update_buttons_state()

    def update_buttons_state(self):
        state = 'disabled' if self.is_tag_filtered or self.is_date_filtered else 'normal'
        self.add_button.configure(state=state)
        self.add_tag_button.configure(state=state)
        self.remove_tag_button.configure(state=state)
        self.tag_entry.configure(state=state)

    # エクスポート機能
    def show_export_dialog(self):
        ExportDialog(self.root, self)

    def export_memos(self, selected_only=False, filtered_only=False, filtered_ids=None):
        """
        メモをエクスポートする
        
        Args:
            selected_only (bool): 選択中のメモのみエクスポートする場合True
            filtered_only (bool): フィルター中のメモのみエクスポートする場合True
            filtered_ids (list): フィルター中のメモIDのリスト
        """
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                if selected_only and self.current_memo_id:
                    self.memo_manager.export_memos(file_path, [self.current_memo_id])
                elif filtered_only and filtered_ids:
                    self.memo_manager.export_memos(file_path, filtered_ids)
                else:
                    self.memo_manager.export_memos(file_path)
                messagebox.showinfo("エクスポート完了", "メモをエクスポートしました。")
        except Exception as e:
            messagebox.showerror("エラー", f"エクスポート中にエラーが発生しました：{str(e)}")

    def import_file(self):
        """XMLファイルから既存のメモリストにメモをインポートする"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("XMLファイル", "*.xml"), ("すべてのファイル", "*.*")]
            )
            if file_path:
                # 一時的なMemoManagerを作成してファイルを読み込む
                temp_manager = MemoManager()
                temp_manager.load_from_file(file_path)
                
                # 既存のメモIDの最大値を取得
                next_id = max([int(id) for id in self.memo_manager.memos.keys()], default=-1) + 1
                
                # 新しいメモを追加
                for memo in temp_manager.memos.values():
                    memo_id = str(next_id)
                    self.memo_manager.memos[memo_id] = memo
                    self.tree.insert('', 'end', memo_id, 
                                   values=(memo.title, memo.date, ', '.join(sorted(memo.tags))))
                    next_id += 1
                
                messagebox.showinfo("インポート完了", "メモをインポートしました。")
        except Exception as e:
            messagebox.showerror("エラー", f"インポート中にエラーが発生しました：{str(e)}")

class ExportDialog:
    def __init__(self, parent, app):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("エクスポート設定")
        self.dialog.geometry("300x200")  # サイズを調整
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.export_frame = ttk.LabelFrame(self.dialog, text="エクスポート範囲", padding=10)
        self.export_frame.pack(fill='x', padx=10, pady=5)
        
        self.export_var = tk.StringVar(value="all")
        ttk.Radiobutton(self.export_frame, text="すべてのメモ", 
                       variable=self.export_var, value="all").pack(anchor='w')
        ttk.Radiobutton(self.export_frame, text="選択中のメモのみ", 
                       variable=self.export_var, value="selected").pack(anchor='w')
        # フィルター中のメモのエクスポートオプションを追加
        ttk.Radiobutton(self.export_frame, text="フィルター中のメモ", 
                       variable=self.export_var, value="filtered",
                       state='normal' if app.is_tag_filtered or app.is_date_filtered else 'disabled'
                       ).pack(anchor='w')
        
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="キャンセル", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        ttk.Button(button_frame, text="エクスポート", 
                  command=lambda: self.export(app)).pack(side='right')

    def export(self, app):
        export_type = self.export_var.get()
        self.dialog.destroy()
        
        if export_type == "selected":
            app.export_memos(selected_only=True)
        elif export_type == "filtered":
            # フィルター中のメモをエクスポート
            filtered_ids = [item for item in app.tree.get_children()]
            app.export_memos(filtered_only=True, filtered_ids=filtered_ids)
        else:  # "all"
            app.export_memos()

class TagFilterDialog:
    def __init__(self, parent, app):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("タグでフィルター")
        self.dialog.geometry("300x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.tag_frame = ttk.LabelFrame(self.dialog, text="フィルターするタグを選択", padding=10)
        self.tag_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.tag_listbox = tk.Listbox(self.tag_frame, selectmode=tk.MULTIPLE)
        self.tag_listbox.pack(fill='both', expand=True)

        for tag in app.memo_manager.get_all_tags():
            self.tag_listbox.insert(tk.END, tag)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="フィルター解除", 
                  command=lambda: self.apply_filter(app, None)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="キャンセル", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        ttk.Button(button_frame, text="実行", 
                  command=lambda: self.apply_filter(app)).pack(side='right')

    def apply_filter(self, app, selected_tags=None):
        if selected_tags is None and self.tag_listbox.curselection():
            selected_tags = [self.tag_listbox.get(i) for i in self.tag_listbox.curselection()]
        
        app.apply_tag_filter(selected_tags)
        self.dialog.destroy()

class DateFilterDialog:
    def __init__(self, parent, app):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("日付でフィルター")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 日付範囲の取得
        start_date, end_date = app.memo_manager.get_date_range()

        # 日付選択フレーム
        self.date_frame = ttk.LabelFrame(self.dialog, text="日付範囲を選択", padding=10)
        self.date_frame.pack(fill='x', padx=10, pady=5)

        # 開始日
        start_frame = ttk.Frame(self.date_frame)
        start_frame.pack(fill='x', pady=5)
        ttk.Label(start_frame, text="開始日：").pack(side='left')
        self.start_date = DateEntry(start_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, locale='ja_JP',
                                  date_pattern='yyyy/mm/dd')
        if start_date:
            self.start_date.set_date(datetime.strptime(start_date, '%Y/%m/%d').date())
        self.start_date.pack(side='left', padx=5)

        # 終了日
        end_frame = ttk.Frame(self.date_frame)
        end_frame.pack(fill='x', pady=5)
        ttk.Label(end_frame, text="終了日：").pack(side='left')
        self.end_date = DateEntry(end_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2, locale='ja_JP',
                                date_pattern='yyyy/mm/dd')
        if end_date:
            self.end_date.set_date(datetime.strptime(end_date, '%Y/%m/%d').date())
        self.end_date.pack(side='left', padx=5)

        # ボタンフレーム
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="フィルター解除", 
                  command=lambda: self.apply_filter(app, None, None)).pack(side='left', padx=5)
        ttk.Button(button_frame, text="キャンセル", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        ttk.Button(button_frame, text="実行", 
                  command=lambda: self.apply_filter(app, self.start_date.get_date().strftime('%Y/%m/%d'), 
                                                  self.end_date.get_date().strftime('%Y/%m/%d'))).pack(side='right')

    def apply_filter(self, app, start_date=None, end_date=None):
        if start_date is None and end_date is None:
            app.apply_date_filter("", "")
        else:
            app.apply_date_filter(start_date, end_date)
        self.dialog.destroy()

class SearchDialog:
    def __init__(self, parent, app):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("メモを検索")
        self.dialog.geometry("400x180")
        self.dialog.transient(parent)
        
        self.app = app
        self.search_results = []
        self.current_result_index = -1
        
        # 検索フレーム
        search_frame = ttk.Frame(self.dialog, padding=10)
        search_frame.pack(fill='x')
        
        ttk.Label(search_frame, text="検索内容：").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='left', padx=5)
        
        # 検索結果表示ラベル
        self.result_label = ttk.Label(self.dialog, text="")
        self.result_label.pack(fill='x', padx=10)
        
        # ボタンフレーム
        button_frame = ttk.Frame(self.dialog, padding=10)
        button_frame.pack(fill='x')
        
        self.prev_button = ttk.Button(button_frame, text="前の項目", command=self.prev_result, state='disabled')
        self.prev_button.pack(side='left', padx=5)
        
        self.next_button = ttk.Button(button_frame, text="次の項目", command=self.next_result, state='disabled')
        self.next_button.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="実行", command=self.execute_search).pack(side='right', padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self.close_dialog).pack(side='right', padx=5)
        
        self.search_entry.focus_set()
        self.dialog.bind('<Return>', lambda e: self.execute_search())
        self.dialog.protocol("WM_DELETE_WINDOW", self.close_dialog)

    def execute_search(self):
        search_text = self.search_var.get()
        if not search_text:
            return
            
        # 大文字小文字を区別しない検索を実行
        self.search_results = self.app.memo_manager.search_memos(search_text, case_sensitive=False)
        self.current_result_index = -1
        
        if self.search_results:
            self.next_result()
            self.update_button_states()
            self.result_label.config(text=f"{len(self.search_results)}件見つかりました。")
        else:
            self.result_label.config(text="見つかりませんでした。")

    def close_dialog(self):
        # ハイライトを解除
        self.app.text_area.tag_remove('search', '1.0', tk.END)
        self.dialog.destroy()

    def next_result(self):
        if not self.search_results:
            return
            
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
        self.show_current_result()
        self.update_button_states()

    def prev_result(self):
        if not self.search_results:
            return
            
        self.current_result_index = (self.current_result_index - 1) % len(self.search_results)
        self.show_current_result()
        self.update_button_states()

    def show_current_result(self):
        if not (0 <= self.current_result_index < len(self.search_results)):
            return

        memo_id, start, end, is_title = self.search_results[self.current_result_index]
        memo = self.app.memo_manager.memos[memo_id]
        
        # メモを選択してテキストエリアを更新
        self.app.tree.selection_set(memo_id)
        self.app.tree.see(memo_id)
        self.app.on_tree_select(None)
        
        # テキストエリアの更新を待つ
        self.dialog.after(10, lambda: self._highlight_text(start, end, is_title))

    def _highlight_text(self, start, end, is_title):
        try:
            self.app.text_area.tag_remove('search', '1.0', tk.END)
            self.app.text_area.tag_config('search', background='yellow')

            # タイトルとコンテンツの位置を計算
            if is_title:
                start_pos = f"1.{start}"
                end_pos = f"1.{end}"
            else:
                # コンテンツ内の位置を計算（タイトル行を考慮）
                content = self.app.text_area.get('1.0', tk.END)
                lines = content[:start].count('\n') + 1
                start_col = start - content[:start].rindex('\n') - 1 if '\n' in content[:start] else start
                end_col = end - content[:end].rindex('\n') - 1 if '\n' in content[:end] else end
                start_pos = f"{lines}.{start_col}"
                end_pos = f"{lines}.{end_col}"

            # ハイライトを適用
            self.app.text_area.tag_add('search', start_pos, end_pos)
            self.app.text_area.see(start_pos)
            self.app.text_area.focus_set()
            self.app.text_area.mark_set(tk.INSERT, start_pos)
        except Exception as e:
            messagebox.showerror("エラー", f"検索結果のハイライト中にエラーが発生しました：{str(e)}")

    def update_button_states(self):
        state = 'normal' if self.search_results else 'disabled'
        self.prev_button.configure(state=state)
        self.next_button.configure(state=state)

class TagSelectionDialog:
    def __init__(self, parent, app, title, callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.tag_frame = ttk.LabelFrame(self.dialog, text="タグを選択", padding=10)
        self.tag_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.tag_listbox = tk.Listbox(self.tag_frame, selectmode=tk.MULTIPLE)
        self.tag_listbox.pack(fill='both', expand=True)

        if title == "削除するタグを選択":
            tags = sorted(app.memo_manager.memos[app.current_memo_id].tags)
        else:
            tags = app.memo_manager.get_all_tags()

        for tag in tags:
            self.tag_listbox.insert(tk.END, tag)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="キャンセル", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        ttk.Button(button_frame, text="実行", 
                  command=lambda: self.apply_selection(callback)).pack(side='right')

    def apply_selection(self, callback):
        selected_tags = [self.tag_listbox.get(i) for i in self.tag_listbox.curselection()]
        self.dialog.destroy()
        callback(selected_tags)
