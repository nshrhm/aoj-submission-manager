# aoj-submission-manager

Aizu Online Judge (AOJ)の提出記録を管理するツール群 - 提出プログラムのダウンロード、成績の追跡、Excel形式でのレポート出力に対応

## AOJについて

[Aizu Online Judge](https://onlinejudge.u-aizu.ac.jp/courses/list)は会津大学が提供するプログラミング学習システムです。課題の提出と自動採点が可能で、プログラミング教育に広く活用されています。

詳しい利用方法は[AIZU_ONLINE_JUDGE.md](AIZU_ONLINE_JUDGE.md)を参照してください。

## セットアップ

1. リポジトリのクローン
2. 必要なライブラリのインストール
   ```bash
   pip install requests
   ```
3. 設定ファイルの準備
   - `users_sample.csv` を `user.csv` としてコピー
     ```bash
     cp users_sample.csv user.csv
     ```
   - `user.csv` に実際の学生情報を入力
   - `prob.csv` に課題の問題IDを設定

## 機能と使用方法

### 1. 提出状況の確認・更新（check_submission.py）

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

- 実行時に自動でバックアップ（`user_YYYYMMDD_NNN.csv`）を作成
- APIから各学生の最新の提出状況を取得
- スコア・提出日時・judgeIdを記録
- 更新情報を問題ID順に表示
  - 各問題IDごとに更新があった学籍番号を一覧表示
  - 例：
    ```
    ITP1_3_A
    dummy001, dummy002, dummy003

    ITP1_3_B
    dummy001, dummy002
    ```
- `--init`：全データを初期状態にリセット
- `--clean`：データ形式の正規化（不正な値の補正）
- `--debug`：処理の詳細を表示

### 2. 提出プログラムのダウンロード（download_all_submissions.py）

```bash
python3 download_all_submissions.py
```

- `downloads/` ディレクトリに保存
- ファイル名形式：`学籍番号_問題ID.py`
  例：`student01_ITP1_1_A.py`
- 100点の提出のみダウンロード対象
- judgeIdを使用して最新の提出を取得
- 既存ファイルは上書き

### 3. Excel用レポート出力（export_excel.py）

```bash
# デフォルト出力（scores_for_excel.tsv）
python3 export_excel.py

# 出力ファイル指定
python3 export_excel.py -o scores.tsv

# 入力ファイル指定
python3 export_excel.py -i user.csv -p prob.csv
```

- タブ区切り形式で出力
- 1行のフォーマット：
  `学籍番号  氏名  問題1スコア  問題1提出日時  問題2スコア ...`
- 日時形式：`YYYY年MM月DD日HH時MM分SS秒`
- Excelで開くと自動的に表形式で表示

### 4. ランキング集計（generate_rankings.py）

```bash
# ランキングを生成
python3 generate_rankings.py
```

- 総合ランキングおよび問題ごとのランキングをTSVファイルとして出力
- 総合ランキング：`rankings/total_ranking_YYYYMMDD.tsv`
  - 同一得点の学生には同一順位を割り当て
- 問題ごとのランキング：`rankings/ITP1_1_A_ranking_YYYYMMDD.tsv`など
  - 提出日時順にランキング
- デバッグログ：`rankings/debug_log_total_ranking.txt`

## ファイル構成

- `user.csv`：学生情報と提出記録（※個人情報を含むため要管理）
  - 形式：学籍番号,姓,名,AOJユーザーID,スコア,提出日時,judgeId,...
  - 1問題につき3列（スコア・提出日時・judgeId）
- `prob.csv`：課題として指定する問題ID
  - 1行目にカンマ区切りで問題IDを列挙
  - 例：`ITP1_1_A,ITP1_1_B,ITP1_1_C`
- `check_submission.py`：提出状況の確認・更新
- `download_all_submissions.py`：ソースコードのダウンロード
- `export_excel.py`：Excel用レポート出力
- `generate_rankings.py`：ランキング集計とTSV出力
- `users_sample.csv`：user.csvのサンプル

## 利用上の注意

- 個人情報管理
  - `user.csv` は `.gitignore` で管理対象外
  - バックアップファイル（`user_*.csv`）も同様
  - サンプルファイル（`users_sample.csv`）使用時は実データを削除

- AOJの利用規約に従う
  - [コース一覧](https://onlinejudge.u-aizu.ac.jp/courses/list)から適切な問題を選択
  - 授業での活用方法は[AIZU_ONLINE_JUDGE.md](AIZU_ONLINE_JUDGE.md)を参照

## 参考資料

- [AIZU_ONLINE_JUDGE.md](AIZU_ONLINE_JUDGE.md)：AOJの利用ガイド
  - ユーザー登録方法
  - コースの選択方法
  - 授業での活用例
