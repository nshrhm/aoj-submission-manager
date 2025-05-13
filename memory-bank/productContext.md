# Product Context

## ツール構成と機能詳細

### 1. 提出状況確認・更新（check_submission.py）

#### 機能概要
- AOJ APIを使用して最新の提出状況を取得
- user.csvの自動更新
- バックアップファイルの自動作成

#### 使用方法
```bash
# 通常実行（user.csvの更新）
python3 check_submission.py

# データ初期化
python3 check_submission.py --init

# データ正規化
python3 check_submission.py --clean

# デバッグ情報表示
python3 check_submission.py --debug
```

#### データ管理
- バックアップ形式: user_YYYYMMDD_NNN.csv
- 自動バックアップによるデータ保護
- 不正値の自動補正機能

#### 表示形式
- 更新情報を問題ID順にソート
- 各問題IDごとに更新があった学籍番号を一覧表示
- 例：
  ```
  ITP1_3_A
  dummy001, dummy002, dummy003
  ```

### 2. 提出プログラム管理（download_all_submissions.py）

#### 機能概要
- AOJから提出されたプログラムを自動ダウンロード
- 100点の提出のみを対象
- 最新の提出を管理

#### 使用方法
```bash
python3 download_all_submissions.py
```

#### ファイル管理
- 保存先: downloads/ディレクトリ
- ファイル名形式: 学籍番号_問題ID.py
- 例: student01_ITP1_1_A.py

### 3. Excel用レポート出力（export_excel.py）

#### 機能概要
- スコアと提出日時の一覧作成
- タブ区切りTSV形式での出力
- Excel互換の表形式

#### 使用方法
```bash
# デフォルト出力
python3 export_excel.py

# 出力ファイル指定
python3 export_excel.py -o scores.tsv

# 入力ファイル指定
python3 export_excel.py -i user.csv -p prob.csv
```

#### 出力形式
- 1行フォーマット: 学籍番号 氏名 問題1スコア 問題1提出日時 問題2スコア ...
- 日時形式: YYYY/MM/DD HH:MM:SS
- 未提出の扱い: "未提出"と表示

## ユーザーワークフロー

### 初期セットアップ
1. リポジトリのクローン
2. requestsライブラリのインストール
3. 設定ファイルの準備
   - users_sample.csv → user.csv
   - prob.csvの問題ID設定

### 定期的な更新作業
1. 提出状況の確認（check_submission.py）
2. 必要に応じてプログラムダウンロード
3. Excel用レポート出力
4. データの確認と分析

### エラー対応
- データ不整合: --clean オプションで正規化
- 初期化必要時: --init オプションで再設定
- トラブル解析: --debug オプションで詳細表示
