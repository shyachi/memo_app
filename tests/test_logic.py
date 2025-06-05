import os
import tempfile
import unittest

from logic import MemoManager


class TestMemoManager(unittest.TestCase):
    def test_add_memo_unique_ids_after_deletions(self):
        manager = MemoManager()
        id0 = manager.add_memo()
        id1 = manager.add_memo()
        id2 = manager.add_memo()
        self.assertEqual(id0, "0")
        self.assertEqual(id1, "1")
        self.assertEqual(id2, "2")
        # Delete middle memo and add another
        manager.delete_memo(id1)
        new_id = manager.add_memo()
        # new id should not reuse deleted id but increment
        self.assertEqual(new_id, "3")
        self.assertEqual(set(manager.memos.keys()), {"0", "2", "3"})

    def test_save_and_load_preserves_data(self):
        manager = MemoManager()
        id0 = manager.add_memo()
        manager.memos[id0].title = "First"
        manager.memos[id0].date = "2024/01/01"
        manager.memos[id0].content = "Alpha"
        manager.memos[id0].tags = {"a", "b"}

        id1 = manager.add_memo()
        manager.memos[id1].title = "Second"
        manager.memos[id1].date = "2024/02/02"
        manager.memos[id1].content = "Beta"
        manager.memos[id1].tags = {"c"}

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name
        try:
            manager.save_to_file(temp_path)

            loaded = MemoManager()
            loaded.load_from_file(temp_path)

            self.assertEqual(len(loaded.memos), 2)
            for i, orig_id in enumerate(sorted(manager.memos.keys())):
                loaded_memo = loaded.memos[str(i)]
                orig_memo = manager.memos[orig_id]
                self.assertEqual(loaded_memo.title, orig_memo.title)
                self.assertEqual(loaded_memo.date, orig_memo.date)
                self.assertEqual(loaded_memo.content, orig_memo.content)
                self.assertEqual(loaded_memo.tags, orig_memo.tags)
        finally:
            os.remove(temp_path)

    def test_filter_by_date(self):
        manager = MemoManager()
        id0 = manager.add_memo()
        manager.memos[id0].date = "2023/09/01"
        id1 = manager.add_memo()
        manager.memos[id1].date = "2023/09/15"
        id2 = manager.add_memo()
        manager.memos[id2].date = "2023/09/20"

        result = manager.filter_by_date("2023/09/10", "2023/09/20")
        self.assertEqual(set(result), {id1, id2})

    def test_search_memos_title_and_content(self):
        manager = MemoManager()
        id0 = manager.add_memo()
        manager.memos[id0].title = "Shopping list"
        manager.memos[id0].content = "Buy milk and eggs"
        id1 = manager.add_memo()
        manager.memos[id1].title = "Work notes"
        manager.memos[id1].content = "Finish the report"

        res_title = manager.search_memos("shop")
        self.assertTrue(any(r[0] == id0 and r[3] for r in res_title))

        res_content = manager.search_memos("report")
        self.assertTrue(any(r[0] == id1 and not r[3] for r in res_content))

        res_content2 = manager.search_memos("milk")
        self.assertTrue(any(r[0] == id0 and not r[3] for r in res_content2))


if __name__ == "__main__":
    unittest.main()
