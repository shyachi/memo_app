import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Dict, Set, Optional

class Memo:
    def __init__(self, title: str, date: str, content: str = "", tags: Optional[Set[str]] = None):
        self.title = title
        self.date = date
        self.content = content
        self.tags = tags or set()

class MemoManager:
    def __init__(self):
        self.memos: Dict[str, Memo] = {}
        self.current_file: Optional[str] = None

    def add_memo(self) -> str:
        memo_id = str(len(self.memos))
        title = "新規メモ"
        date = datetime.now().strftime('%Y/%m/%d')
        self.memos[memo_id] = Memo(title, date)
        return memo_id

    def delete_memo(self, memo_id: str) -> bool:
        if memo_id in self.memos:
            del self.memos[memo_id]
            return True
        return False

    def get_all_tags(self) -> list[str]:
        all_tags = set()
        for memo in self.memos.values():
            all_tags.update(memo.tags)
        return sorted(all_tags)

    def get_date_range(self) -> tuple[str, str]:
        """メモの日付の範囲を取得"""
        if not self.memos:
            return "", ""
        dates = [memo.date for memo in self.memos.values()]
        return min(dates), max(dates)

    def filter_by_date(self, start_date: str, end_date: str) -> list[str]:
        """指定された日付範囲内のメモIDを取得"""
        print(f"filter_by_date: start={start_date}, end={end_date}")
        filtered_ids = []
        for memo_id, memo in self.memos.items():
            print(f"checking memo {memo_id}: date={memo.date}")
            if start_date <= memo.date <= end_date:
                print(f"memo {memo_id} matches filter")
                filtered_ids.append(memo_id)
        print(f"filtered_ids: {filtered_ids}")
        return filtered_ids

    def save_to_file(self, file_path: str) -> None:
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
        with open(file_path, 'w', encoding='utf-8') as file:
            if memo_ids:
                # 選択されたメモのみエクスポート
                for memo_id in memo_ids:
                    if memo_id in self.memos:
                        memo = self.memos[memo_id]
                        self._write_memo_to_file(file, memo)
            else:
                # すべてのメモをエクスポート
                for memo in self.memos.values():
                    self._write_memo_to_file(file, memo)
                    file.write("-" * 50 + "\n")

    def _write_memo_to_file(self, file, memo: Memo) -> None:
        file.write(f"タイトル: {memo.title}\n")
        file.write(f"日付: {memo.date}\n")
        file.write(f"タグ: {', '.join(sorted(memo.tags))}\n")
        file.write(f"内容:\n{memo.content}\n")
