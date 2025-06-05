# Memo App

## コードベース概要 (Japanese)

### コード構造
1. **main.py**: アプリケーションのエントリポイント。Tkinter でウィンドウを生成し、`MemoApp` を起動します。
2. **logic.py**: `Memo` と `MemoManager` クラスを定義し、メモの追加・削除、保存/読み込み、検索などのロジックを管理します。
3. **ui.py**: Tkinter と tkcalendar を使って GUI を構築します。メモの一覧表示や編集、タグ・日付フィルタ、検索ダイアログなどの処理を担当します。

### 知っておくべき重要事項
- **依存ライブラリ**: Tkinter (標準ライブラリ) と `tkcalendar` を使用します。`tkcalendar` は事前にインストールしてください。
- **データ保存形式**: メモは XML 形式で保存されます。テキスト形式へのエクスポートも可能です。
- **検索・フィルタ機能**: タグや日付によるフィルタやキーワード検索が実装されています。
- **ライセンス**: MIT License で公開されています。

### 次に学習すると良い内容
1. `logic.py` を読んでメモ管理の基本機能を理解する。
2. `ui.py` のイベント処理を追い、`MemoManager` とどう連携しているか確認する。
3. `tkcalendar` の使い方を習得し、日付選択処理を理解する。
4. 依存関係をインストールした上で `python main.py` を実行し、実際に動作を確認する。

## Overview (English)

### Structure
1. **main.py** – Entry point that creates the Tkinter window and launches `MemoApp`.
2. **logic.py** – Defines `Memo` and `MemoManager` for adding/removing memos, saving/loading to file, and search logic.
3. **ui.py** – Builds the GUI using Tkinter and tkcalendar. Handles list display, editing, tag/date filters and search dialogs.

### Key Points
- **Dependencies**: Uses Tkinter and the external package `tkcalendar`. Install `tkcalendar` before running.
- **Data format**: Memos are stored in XML. Export to plain text is also supported.
- **Search and filter**: Tag and date filters and keyword search are implemented.
- **License**: Distributed under the MIT License.

### Suggested next steps
1. Read `logic.py` to learn how memo management works.
2. Follow event handling in `ui.py` to see how it cooperates with `MemoManager`.
3. Learn the basics of `tkcalendar` for date selection features.
4. Install dependencies and run `python main.py` to try the GUI.

## Usage

### Installation
1. Clone this repository.
2. Install the required package:
   ```bash
   pip install tkcalendar
   ```

### Run the application
Execute the following command:
```bash
python main.py
```
This will start the Tkinter-based memo application.

### Run tests
The project includes unit tests for `MemoManager`. Run them with:
```bash
python -m unittest discover tests
```
