import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, Set, Optional

# メモの基本データを管理するクラス
class Memo:
    """
    メモの基本情報を保持するクラス
    
    Attributes:
        title (str): メモのタイトル
        date (str): メモの作成/更新日付（YYYY/MM/DD形式）
        content (str): メモの本文
        tags (Set[str]): メモに付けられたタグのセット
    """
    def __init__(self, title: str, date: str, content: str = "", tags: Optional[Set[str]] = None):
        self.title = title
        self.date = date
        self.content = content
        self.tags = tags or set()

class MemoManager:
    """
    メモの作成、保存、読み込みなどの操作を管理するクラス
    
    Attributes:
        memos (Dict[str, Memo]): メモIDをキーとするメモオブジェクトの辞書
        current_file (Optional[str]): 現在開いているファイルのパス
    """
    def __init__(self):
        self.memos: Dict[str, Memo] = {}
        self.current_file: Optional[str] = None

    def add_memo(self) -> str:
        """
        新規メモを作成する

        Returns:
            str: 作成されたメモのID

        Note:
            メモIDは既存IDの数値部分の最大値に1を加えて生成される
        """
        memo_id = str(max(map(int, self.memos.keys()), default=-1) + 1)
        title = "新規メモ"
        date = datetime.now().strftime('%Y/%m/%d')
        self.memos[memo_id] = Memo(title, date)
        return memo_id

    def delete_memo(self, memo_id: str) -> bool:
        """
        指定されたIDのメモを削除する
        
        Args:
            memo_id (str): 削除するメモのID
            
        Returns:
            bool: 削除が成功した場合はTrue、メモが存在しない場合はFalse
        """
        if memo_id in self.memos:
            del self.memos[memo_id]
            return True
        return False

    def get_all_tags(self) -> list[str]:
        """
        すべてのメモから一意のタグを収集し、ソートされたリストとして返す
        
        Returns:
            list[str]: すべてのユニークなタグを含むソート済みリスト
        """
        all_tags = set()
        for memo in self.memos.values():
            all_tags.update(memo.tags)
        return sorted(all_tags)

    def get_date_range(self) -> tuple[str, str]:
        """
        すべてのメモの日付範囲を取得する
        
        Returns:
            tuple[str, str]: (最古の日付, 最新の日付)のタプル。メモが存在しない場合は空文字のタプル
        """
        if not self.memos:
            return "", ""
        dates = [memo.date for memo in self.memos.values()]
        return min(dates), max(dates)

    def filter_by_date(self, start_date: str, end_date: str) -> list[str]:
        """
        指定された日付範囲内のメモIDを取得する
        
        Args:
            start_date (str): 開始日（YYYY/MM/DD形式）
            end_date (str): 終了日（YYYY/MM/DD形式）
            
        Returns:
            list[str]: 日付範囲内のメモIDのリスト
        """
        filtered_ids = []
        for memo_id, memo in self.memos.items():
            if start_date <= memo.date <= end_date:
                filtered_ids.append(memo_id)
        return filtered_ids

    def save_to_file(self, file_path: str) -> None:
        """
        メモをXMLファイルに保存する
        
        Args:
            file_path (str): 保存先のファイルパス
        """
        root = ET.Element("memos")
        for memo_id, memo in self.memos.items():
            memo_elem = ET.SubElement(root, "memo")
            name = ET.SubElement(memo_elem, "name")
            name.text = memo.title
            date = ET.SubElement(memo_elem, "date")
            date.text = memo.date
            content = ET.SubElement(memo_elem, "content")
            content.text = memo.content
            tags = ET.SubElement(memo_elem, "tags")
            tags.text = ','.join(sorted(memo.tags))

        xml_str = minidom.parseString(ET.tostring(root, 'utf-8')).toprettyxml(indent="    ")
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(xml_str)
        
        self.current_file = file_path

    def load_from_file(self, file_path: str) -> None:
        """
        XMLファイルからメモを読み込む
        
        Args:
            file_path (str): 読み込むファイルのパス
        """
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        self.memos.clear()
        
        for i, memo_elem in enumerate(root.findall('memo')):
            memo_id = str(i)
            title = memo_elem.find('name').text or "新規メモ"
            date_text = memo_elem.find('date').text if memo_elem.find('date') is not None else datetime.now().strftime('%Y/%m/%d')
            content = memo_elem.find('content').text or ""
            tags_text = memo_elem.find('tags').text if memo_elem.find('tags') is not None else ""
            tags = set(filter(None, tags_text.split(','))) if tags_text else set()
            
            self.memos[memo_id] = Memo(title, date_text, content, tags)
        
        self.current_file = file_path

    def export_memos(self, file_path: str, memo_ids: Optional[list[str]] = None) -> None:
        """
        メモをテキストファイルにエクスポートする
        
        Args:
            file_path (str): エクスポート先のファイルパス
            memo_ids (Optional[list[str]]): エクスポートするメモのIDリスト。Noneの場合は全メモをエクスポート
        """
        with open(file_path, 'w', encoding='utf-8') as file:
            target_memos = []
            if memo_ids:
                # 選択されたメモのみエクスポート
                target_memos = [self.memos[memo_id] for memo_id in memo_ids if memo_id in self.memos]
            else:
                # すべてのメモをエクスポート
                target_memos = list(self.memos.values())

            for i, memo in enumerate(target_memos):
                self._write_memo_to_file(file, memo)
                # 最後のメモ以外は区切り線を追加
                if i < len(target_memos) - 1:
                    file.write("-" * 50 + "\n")

    def _write_memo_to_file(self, file, memo: Memo) -> None:
        """
        メモの内容をファイルに書き込む（内部メソッド）
        
        Args:
            file: 書き込み先のファイルオブジェクト
            memo (Memo): 書き込むメモオブジェクト
        """
        file.write(f"タイトル: {memo.title}\n")
        file.write(f"日付: {memo.date}\n")
        file.write(f"タグ: {', '.join(sorted(memo.tags))}\n")
        file.write(f"内容:\n{memo.content}\n")

    def search_memos(self, search_text: str, case_sensitive: bool = False) -> list[tuple[str, int, int, bool]]:
        """
        メモの内容を検索する
        
        Args:
            search_text (str): 検索するテキスト
            case_sensitive (bool): 大文字小文字を区別するかどうか（デフォルトはFalse）
            
        Returns:
            list[tuple[str, int, int, bool]]: (メモID, 開始位置, 終了位置, タイトル内フラグ)のリスト
        """
        if not search_text:
            return []

        results = []
        search_len = len(search_text)

        # 大文字小文字を区別しない場合は検索テキストを小文字に変換
        if not case_sensitive:
            search_text = search_text.lower()

        for memo_id, memo in self.memos.items():
            # タイトル内を検索
            title = memo.title if case_sensitive else memo.title.lower()
            title_start = 0
            while title_start <= len(title) - search_len:
                pos = title.find(search_text, title_start)
                if pos == -1:
                    break
                results.append((memo_id, pos, pos + search_len, True))
                title_start = pos + search_len
            
            # 内容を検索
            content = memo.content if case_sensitive else memo.content.lower()
            content_start = 0
            while content_start <= len(content) - search_len:
                pos = content.find(search_text, content_start)
                if pos == -1:
                    break
                results.append((memo_id, pos, pos + search_len, False))
                content_start = pos + search_len
        
        return results
