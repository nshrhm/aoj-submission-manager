#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file check_submission.py
@brief AOJの提出記録を確認し、ユーザーごとのスコア・提出日時・judgeIdを更新・初期化するプログラム

このプログラムは、Aizu Online Judge (AOJ) のAPIを使用して
各ユーザーの問題ごとの最高スコア、提出日時（UNIXタイムスタンプミリ秒）、judgeIdを取得し、
user.csvに反映します。

--init: user.csvを初期状態にリセット
--clean: user.csvのデータを正規化して再保存
--debug: デバッグ情報を表示
"""

import requests
import csv
import os
import urllib3
import argparse
from datetime import datetime
from typing import List, Tuple

# SSL警告を抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# AOJ APIのエンドポイント
ENDPOINT = 'https://judgeapi.u-aizu.ac.jp'
URI = '/submission_records'

# 未設定時の値
NO_SUBMISSION = -1

def debug_print(msg: str, debug: bool = False):
    """デバッグモード時のみメッセージを出力"""
    if debug:
        print(f"DEBUG: {msg}")

def get_max_info(user_id: str, prob_id: str, debug: bool = False) -> tuple[int, int, int]:
    """
    指定ユーザー・問題の提出記録を取得し、
    最高スコア、最新提出日時（ミリ秒）、judgeIdを返す。

    @param user_id AOJユーザーID
    @param prob_id AOJ問題ID
    @param debug デバッグ情報を表示するか
    @return (max_score, submission_timestamp, judge_id)
    """
    url = f"{ENDPOINT}{URI}/users/{user_id}/problems/{prob_id}"
    max_score, max_date, max_jid = 0, 0, NO_SUBMISSION
    try:
        resp = requests.get(url, verify=False, timeout=10)
        data = resp.json() or []
        debug_print(f"{prob_id}: データ数 {len(data)}", debug)

        for sub in data:
            score = sub.get("score", 0)
            date = sub.get("submissionDate", 0)
            jid = sub.get("judgeId", NO_SUBMISSION)

            # 数値に変換（変換失敗時は初期値）
            try:
                score = int(score)
            except (ValueError, TypeError):
                score = 0
            try:
                date = int(date)
            except (ValueError, TypeError):
                date = 0
            try:
                jid = int(jid)
            except (ValueError, TypeError):
                jid = NO_SUBMISSION

            debug_print(f"{prob_id}: スコア={score} 日時={date} ID={jid}", debug)

            # スコアが更新、または同スコアで日時が新しい場合に更新
            if score > max_score or (score == max_score and date > max_date):
                max_score = score
                max_date = date
                max_jid = jid
                debug_print(f"{prob_id}: 更新 → スコア={max_score} 日時={max_date} ID={max_jid}", debug)

    except Exception as e:
        print(f"エラー: {prob_id}の取得中にエラーが発生しました - {e}")

    debug_print(f"{prob_id}: 最終結果 → スコア={max_score} 日時={max_date} ID={max_jid}", debug)
    return max_score, max_date, max_jid

def backup_user_csv() -> str:
    """
    user.csvのバックアップを作成し、バックアップファイル名を返す。
    """
    date_str = datetime.now().strftime("%Y%m%d")
    n = 1
    while True:
        name = f"user_{date_str}_{n:03d}.csv"
        if not os.path.exists(name):
            break
        n += 1
    with open("user.csv", "r") as src, open(name, "w") as dst:
        dst.write(src.read())
    return name

def initialize_user_csv():
    """
    user.csvを初期化し、各問題のスコア・提出日時・judgeIdを初期値にリセットする。
    """
    with open("user.csv", "r", newline="") as f:
        rows = list(csv.reader(f))
    with open("prob.csv", "r", newline="") as f:
        probs = next(csv.reader(f))
    out = []
    for r in rows:
        base = r[:4]  # 学籍番号,姓,名,ユーザーID
        for _ in probs:
            # score, date, judgeIdをそれぞれ初期化
            base.extend(["0", "0", str(NO_SUBMISSION)])
        out.append(base)
    with open("user.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(out)
    print("user.csvを初期化しました。")

def normalize_submission_data(row: List[str], prob_count: int) -> List[str]:
    """
    user.csvの1行のデータを正規化する。
    3列（スコア・提出日時・judgeId）単位でデータを整理し、
    不正な値は初期値に置き換える。

    @param row CSVの1行データ
    @param prob_count 問題数
    @return 正規化されたデータ
    """
    # 基本情報（学籍番号,姓,名,ユーザーID）は保持
    result = row[:4]
    # 残りは3列単位で処理
    for i in range(prob_count):
        base_idx = 4 + i * 3
        # CSVの列が足りない場合は初期値で補完
        if base_idx + 2 >= len(row):
            result.extend(["0", "0", str(NO_SUBMISSION)])
            continue

        # 各値を取得して数値変換
        try:
            score = int(row[base_idx])
        except (ValueError, TypeError):
            score = 0

        try:
            date = int(row[base_idx + 1])
        except (ValueError, TypeError):
            date = 0

        try:
            jid = int(row[base_idx + 2])
        except (ValueError, TypeError):
            jid = NO_SUBMISSION

        # 不正な値の補正
        if score < 0 or score > 100:
            score = 0
        if date < 0:
            date = 0
        if jid < NO_SUBMISSION:
            jid = NO_SUBMISSION

        # 文字列に戻して追加
        result.extend([str(score), str(date), str(jid)])

    return result

def clean_user_csv():
    """
    user.csvのデータを正規化して再保存する。
    """
    # データ読み込み
    with open("user.csv", "r", newline="") as f:
        rows = list(csv.reader(f))
    with open("prob.csv", "r", newline="") as f:
        prob_count = len(next(csv.reader(f)))

    # 各行を正規化
    normalized = [normalize_submission_data(row, prob_count) for row in rows]

    # 保存
    with open("user.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(normalized)

    print("user.csvを正規化しました。")

def main():
    parser = argparse.ArgumentParser(description="user.csvを初期化または提出状況を更新")
    parser.add_argument("--init", action="store_true", help="user.csvを初期化します")
    parser.add_argument("--clean", action="store_true", help="user.csvを正規化します")
    parser.add_argument("--debug", action="store_true", help="デバッグ情報を表示します")
    args = parser.parse_args()

    if args.init:
        initialize_user_csv()
        return

    if args.clean:
        clean_user_csv()
        return

    # バックアップ作成
    bak = backup_user_csv()
    print(f"バックアップを作成しました: {bak}")

    # CSV読み込み
    with open("user.csv", "r", newline="") as f:
        rows = list(csv.reader(f))
    with open("prob.csv", "r", newline="") as f:
        probs = next(csv.reader(f))

    updated = []
    for row in rows:
        print(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}", end="")
        uid = row[3]
        new_row = row[:4]  # 基本情報

        # 1問題につき3列(score,date,judgeId)
        for i, pid in enumerate(probs):
            base_idx = 4 + i * 3  # 各問題の開始インデックス
            # CSVの列が足りない場合は拡張
            while len(row) < base_idx + 3:
                row.extend(["0", "0", str(NO_SUBMISSION)])

            # 現在の値を取得（CSVから）
            cur_score = row[base_idx]
            cur_date = row[base_idx + 1]
            cur_jid = row[base_idx + 2]

            # AOJ APIから最新情報を取得
            max_score, max_date, max_jid = get_max_info(uid, pid, args.debug)

            # 現在のCSVの値を数値に変換
            try:
                cur_score_int = int(cur_score)
            except (ValueError, TypeError):
                cur_score_int = 0

            try:
                cur_date_int = int(cur_date)
            except (ValueError, TypeError):
                cur_date_int = 0

            try:
                cur_jid_int = int(cur_jid)
            except (ValueError, TypeError):
                cur_jid_int = NO_SUBMISSION

            # より良い提出があれば更新
            if (max_score > cur_score_int or 
                (max_score == cur_score_int and max_date > cur_date_int)):
                new_row.extend([str(max_score), str(max_date), str(max_jid)])
                print(f"\t{max_score}({max_date},{max_jid})", end="")
            else:
                # 現在の値を保持
                new_row.extend([str(cur_score_int), str(cur_date_int), str(cur_jid_int)])
                print(f"\t{cur_score_int}({cur_date_int},{cur_jid_int})", end="")

        updated.append(new_row)
        print()

    # 上書き保存
    with open("user.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(updated)
    print("user.csvを更新しました。")

if __name__ == "__main__":
    main()
