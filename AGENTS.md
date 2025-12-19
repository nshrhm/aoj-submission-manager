# AGENTS.md (aoj-submission-manager)

このファイルは、開発用AIエージェント（Copilot / Claude / Cursor / Cline 等）がこのリポジトリを安全に理解・変更できるように、**プロジェクトの不変情報**をまとめたものです。

## 目的
- Aizu Online Judge (AOJ) の提出データを管理・分析するツール群
- 教員/TA が学生の進捗・成績を効率的に把握することを支援

## 主要スクリプト（入口）
- `check_submission.py`
  - AOJ APIから提出状況を取得し、`user.csv` を更新
  - オプション: `--init`（初期化）/ `--clean`（正規化）/ `--debug`（詳細ログ）
- `download_all_submissions.py`
  - 100点の提出のみを対象にソースコードを `downloads/` へダウンロード
- `export_excel.py`
  - Excel向けにTSV（タブ区切り）を出力（デフォルト `scores_for_excel.tsv`）
- `generate_rankings.py`
  - 総合/問題別ランキングを `rankings/` にTSV出力

## 典型ワークフロー（人間/エージェント共通）
1. 依存関係を用意
   - `pip install requests`
2. 入力CSVを用意
   - `users_sample.csv` を `user.csv` にコピーして実データを記入
   - `prob.csv` に対象問題IDを設定（1行目にカンマ区切り）
3. 提出状況を更新
   - `python3 check_submission.py`
4. 必要ならソースコードを回収
   - `python3 download_all_submissions.py`
5. 集計/出力
   - `python3 export_excel.py`
   - `python3 generate_rankings.py`

## データファイルの仕様（重要）
### `user.csv`
- 個人情報を含む（後述）
- 先頭4列: `学籍番号,姓,名,AOJユーザーID`
- 以降は **問題ごとに3列セット** を繰り返す
  - `スコア,提出日時,judgeId`
- 提出日時は内部的にUnix time（ミリ秒）で保持し、出力では `YYYY/MM/DD HH:MM:SS` に変換

### `prob.csv`
- 1行目にカンマ区切りで問題IDを列挙
  - 例: `ITP1_1_A,ITP1_1_B,ITP1_1_C`

### 生成物（コミット対象ではない想定）
- バックアップ: `user_YYYYMMDD_NNN.csv`
- ダウンロード: `downloads/<学籍番号>_<問題ID>.py`
- Excel用出力: `scores_for_excel.tsv` または `scores_*.tsv`
- ランキング: `rankings/*_ranking_YYYYMMDD.tsv`, `rankings/total_ranking_YYYYMMDD.tsv`

## 安全・運用上の注意（必読）
- `user.csv` と `user_*.csv` は**個人情報**を含むため、誤って公開/コミットしないこと。
- `downloads/` / `rankings/` / `scores_*.tsv` 等の生成物も、通常はコミットしない運用を想定（`.gitignore` を尊重）。
- ドキュメントやテストデータに実データを貼らないこと（必要なら匿名化したダミー値を使う）。
- AOJ APIを叩く処理を変更する場合は、不要な再試行や高頻度アクセスを避ける（礼儀・負荷配慮）。

## 変更時の指針（エージェント向け）
- 入出力（CSV/TSVの列順・形式）は利用者の運用に直結するため、変更は最小限にし、必要ならREADME更新まで行う。
- 例外時にも `user.csv` を破壊しない（バックアップや一時ファイル経由など、現行の挙動を尊重）。
- 既存のCLIオプション（`--init/--clean/--debug` など）や出力ファイル命名規則は互換性を優先。

## 参考ドキュメント
- README: セットアップと使い方の一次情報
- `AIZU_ONLINE_JUDGE.md`: AOJの利用ガイド（授業向け説明）
