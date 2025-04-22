#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file download_all_submissions.py
@brief AOJの提出プログラムをダウンロードするプログラム

user.csvから読み取ったjudgeIdを使用して、受講生全員の100点提出を
「学籍番号_問題ID.py」の形式でdownloadsディレクトリにダウンロードします。
"""

import csv
import os
import requests
import urllib3

# SSL警告を抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AOJSubmissionDownloader:
    """AOJの提出プログラムをダウンロードするクラス"""

    def __init__(self):
        self.judge_api = 'https://judgeapi.u-aizu.ac.jp'

    def get_source_code(self, submission_id: int) -> dict:
        """
        指定した提出IDのソースコードをAOJ APIから取得する

        :param submission_id: 提出ID（judgeId）
        :return: ソースコード情報の辞書（取得失敗時はNone）
        """
        url = f"{self.judge_api}/reviews/{submission_id}"
        try:
            response = requests.get(url, verify=False, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"エラー: {submission_id}の取得中にエラーが発生しました - {e}")
        return None

def main():
    # CSV読み込み
    with open('user.csv', 'r', newline='') as f:
        users = list(csv.reader(f))
    with open('prob.csv', 'r', newline='') as f:
        problems = next(csv.reader(f))

    downloader = AOJSubmissionDownloader()
    os.makedirs("downloads", exist_ok=True)

    for user in users:
        student_id = user[0]  # 学籍番号
        fields = user[4:]     # データフィールド（スコア・日時・judgeId）

        # 1問題につき3列
        for i, prob_id in enumerate(problems):
            base_idx = i * 3
            if base_idx + 2 >= len(fields):  # インデックスチェック
                continue

            score = fields[base_idx]
            judge_id = fields[base_idx + 2]

            # 100点の提出のみダウンロード
            if score == "100" and judge_id and judge_id != "0":
                try:
                    submission_id = int(judge_id)
                except ValueError:
                    print(f"{student_id} {prob_id}: judgeId不正 ({judge_id})")
                    continue

                # ソースコード取得
                data = downloader.get_source_code(submission_id)
                if not data or "sourceCode" not in data:
                    print(f"{student_id} {prob_id}: ソースコード取得失敗 (judgeId={submission_id})")
                    continue

                # ファイル保存
                filename = f"downloads/{student_id}_{prob_id}.py"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(data["sourceCode"])
                print(f"{filename} をダウンロードしました。")

if __name__ == "__main__":
    main()
