# Google Spreadsheet + GAS 版

このディレクトリには、`check_submission.py` / `export_excel.py` / `generate_rankings.py` を Google Spreadsheet + Google Apps Script で置き換える実装を置いています。

## 構成

- `appsscript.json`
  - Apps Script のマニフェスト
- `AOJSubmissionManager.gs`
  - シート初期化、AOJ API 同期、Dashboard/Rankings 再構築、TSV 出力、100 点コード保存

## 前提

- Google Spreadsheet を 1 つ用意する
- Apps Script プロジェクトへこのディレクトリのファイルを配置する
- `Students` と `Problems` に対象データを入力する

## `appsscript.json` の置き方

### Apps Script エディタで直接置く

1. Spreadsheet で `拡張機能` → `Apps Script` を開く
2. 左側の `プロジェクトの設定` を開く
3. `アプリスクリプト マニフェスト ファイル (appsscript.json) をエディタで表示` を ON にする
4. 表示された `appsscript.json` に、このリポジトリの `gas/appsscript.json` の内容を貼り付けて保存する
5. `AOJSubmissionManager.gs` も同じ Apps Script プロジェクトへ貼り付ける

### `clasp` で同期する

1. `npm install -g @google/clasp`
2. `clasp login`
3. Spreadsheet から Apps Script プロジェクトを開き、プロジェクト ID を確認する
4. `gas/` を作業ディレクトリとして `.clasp.json` を作成する
5. `clasp push` で `AOJSubmissionManager.gs` と `appsscript.json` を同期する

`.clasp.json` には Apps Script の `scriptId` が入るため、通常はリポジトリへコミットしません。

## シート構成

- `Students`
  - ヘッダー: `studentId, surname, givenName, aojUserId`
- `Problems`
  - ヘッダー: `problemId`
- `BestSubmissions`
  - ヘッダー: `studentId, problemId, score, submissionDateMs, judgeId, updatedAt`
- `Dashboard`
  - Spreadsheet 閲覧用の横持ち表示
- `Rankings`
  - 総合ランキングと問題別ランキング
- `Settings`
  - バッチサイズ、最大実行時間、Drive フォルダ ID など

最初に Spreadsheet を開くと `AOJ Manager` メニューが作成されます。必要なシートが無ければ自動作成されます。

## 使い方

1. `Students` に学生一覧を入力する
2. `Problems` に課題の problem ID を 1 行 1 問で入力する
3. `Initialize Data` を実行して `BestSubmissions` を初期化する
4. `AOJ Sync` を実行して AOJ API から提出状況を取り込む
5. 必要に応じて `Rebuild Dashboard` / `Rebuild Rankings` を実行する
6. TSV が必要なら `Export TSV`、100 点コードの保存が必要なら `Download Accepted Code` を実行する

## 補足

- `AOJ Sync` は `UrlFetchApp.fetchAll()` を使ってまとめて取得します
- 実行時間制限に近づいた場合は途中で止まり、次回の `AOJ Sync` で続きから再開します
- 更新系処理の前には、`Settings.snapshotBeforeMutation=TRUE` のとき `BestSubmissions` を CSV として Drive に退避します
- Drive 保存先は `Settings` の `exportFolderId` / `codeFolderId` / `snapshotFolderId` で指定できます
- `Download Accepted Code` は現行 Python 版に合わせて `studentId_problemId.py` の名前で保存します
- 既存の `user.csv` / `prob.csv` をそのまま読む実装ではないため、Spreadsheet 側の `Students` / `Problems` へ転記して使います
