# Technical Context

## 技術スタック

### 1. 基本環境
- Python 3.x
- Git（バージョン管理）
- AOJ API

### 2. 依存ライブラリ
```bash
requests  # APIリクエスト用
```

### 3. ファイルフォーマット
```
CSV (Comma-Separated Values)
- user.csv: ユーザー情報と提出記録
- prob.csv: 問題ID定義
- バックアップファイル

TSV (Tab-Separated Values)
- scores_for_excel.tsv: Excel用出力
```

## API仕様

### AOJ API
- 提出状況の取得
- ソースコードのダウンロード
- ユーザー情報の取得

## ファイル仕様

### 1. user.csv
```
フォーマット:
学籍番号,姓,名,AOJユーザーID,[問題1スコア,問題1提出日時,問題1judgeId],...]

例:
220001,山田,太郎,user01,100,1650123456789,12345,...
```

### 2. prob.csv
```
フォーマット:
問題ID1,問題ID2,問題ID3,...

例:
ITP1_1_A,ITP1_1_B,ITP1_1_C
```

### 3. scores_for_excel.tsv
```
フォーマット:
学籍番号<TAB>氏名<TAB>問題1スコア<TAB>問題1提出日時<TAB>...

日時形式:
YYYY/MM/DD HH:MM:SS
```

## 開発環境設定

### 1. リポジトリ設定
```bash
# クローン
git clone [repository-url]

# 依存関係インストール
pip install requests
```

### 2. 設定ファイル準備
```bash
# サンプルファイルのコピー
cp users_sample.csv user.csv

# prob.csvの設定
echo "ITP1_1_A,ITP1_1_B,ITP1_1_C" > prob.csv
```

### 3. ディレクトリ構造
```
AOJ_Tools/
├── .gitignore          # Git除外設定
├── README.md           # プロジェクト説明
├── AIZU_ONLINE_JUDGE.md # AOJ利用ガイド
├── check_submission.py # 提出確認スクリプト
├── download_all_submissions.py # ダウンロードスクリプト
├── export_excel.py     # Excel出力スクリプト
├── prob.csv           # 問題定義
├── user.csv          # ユーザーデータ（非Git管理）
└── downloads/        # ダウンロードディレクトリ
```

## データ形式

### 1. 日時形式
```python
# UnixタイムスタンプからYYYY/MM/DD HH:MM:SS形式への変換
datetime.fromtimestamp(int(ms)/1000).strftime('%Y/%m/%d %H:%M:%S')
```

### 2. スコア形式
```
有効範囲: 0-100
特殊値: 
- 0: 未提出または不合格
- 100: 満点合格
```

### 3. エラー値
```
未提出: "未提出"
不正値: 自動的に0に変換
