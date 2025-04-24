#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file export_excel.py
@brief スコアと提出日時をExcel用のタブ区切り形式で出力するプログラム

このプログラムは、user.csvからスコアと提出日時を読み取り、
Excel用のタブ区切りTSVファイルとして出力します。
各行は「学籍番号 氏名 問題1スコア 問題1提出日時 問題2スコア...」という形式です。
日時は「2025/4/22 14:23:45」のような読みやすい形式で出力されます。
"""

import csv
from datetime import datetime
import argparse

def convert_timestamp(ms: int) -> str:
    """
    UNIXタイムスタンプ（ミリ秒）を読みやすい日時文字列に変換

    @param ms UNIXタイムスタンプ（ミリ秒）
    @return 「YYYY/MM/DD HH:MM:SS」形式の文字列
    """
    try:
        dt = datetime.fromtimestamp(int(ms)/1000)
        return dt.strftime('%Y/%m/%d %H:%M:%S')
    except (ValueError, TypeError, OSError):
        return "未提出"

def get_header_row(problems: list) -> str:
    """
    TSVファイルのヘッダー行を生成

    @param problems 問題IDのリスト
    @return タブ区切りのヘッダー行
    """
    header = ["学籍番号", "氏名"]
    for pid in problems:
        header.extend([f"{pid}得点", f"{pid}提出日時"])
    return "\t".join(header)

def format_user_data(user: list, problems: list) -> str:
    """
    1ユーザーの情報を整形

    @param user user.csvの1行（学籍番号,姓,名,ユーザーID,データ...）
    @param problems 問題IDのリスト
    @return タブ区切りの1行データ
    """
    # 基本情報
    student_id = user[0]
    name = f"{user[1]} {user[2]}"
    result = [student_id, name]

    # 各問題のスコアと提出日時
    data_fields = user[4:]  # スコア・提出日時・judgeIdのデータ部分
    for i in range(len(problems)):
        base_idx = i * 3  # 1問題につき3列（スコア・提出日時・judgeId）
        if base_idx + 1 >= len(data_fields):
            # データが足りない場合
            result.extend(["0", "未提出"])
            continue

        score = data_fields[base_idx]
        timestamp = data_fields[base_idx + 1]

        # スコアが0または不正な値の場合
        try:
            score_int = int(score)
            if score_int <= 0:
                result.extend(["0", "未提出"])
                continue
        except (ValueError, TypeError):
            result.extend(["0", "未提出"])
            continue

        # 正常な提出の場合
        result.append(score)
        result.append(convert_timestamp(timestamp))

    return "\t".join(result)

def export_as_excel(input_file: str = "user.csv", 
                   problems_file: str = "prob.csv",
                   output_file: str = "scores_for_excel.tsv") -> None:
    """
    user.csvのデータをExcel用のタブ区切り形式で出力

    @param input_file 入力ファイル（user.csv）
    @param problems_file 問題定義ファイル（prob.csv）
    @param output_file 出力ファイル名
    """
    try:
        # 問題ID一覧を読み込み
        with open(problems_file, "r", newline="") as f:
            problems = next(csv.reader(f))

        # ユーザーデータを読み込み
        with open(input_file, "r", newline="") as f:
            users = list(csv.reader(f))

        # TSV形式で出力
        with open(output_file, "w", encoding="utf-8") as f:
            # ヘッダー行
            f.write(get_header_row(problems) + "\n")
            # データ行
            for user in users:
                f.write(format_user_data(user, problems) + "\n")

        print(f"{output_file} を作成しました。")

    except Exception as e:
        print(f"エラー: ファイルの処理中にエラーが発生しました - {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="スコアと提出日時をExcel用のタブ区切り形式で出力")
    parser.add_argument("-i", "--input", default="user.csv",
                      help="入力ファイル（デフォルト: user.csv）")
    parser.add_argument("-p", "--problems", default="prob.csv",
                      help="問題定義ファイル（デフォルト: prob.csv）")
    parser.add_argument("-o", "--output", default="scores_for_excel.tsv",
                      help="出力ファイル（デフォルト: scores_for_excel.tsv）")
    args = parser.parse_args()

    export_as_excel(args.input, args.problems, args.output)

if __name__ == "__main__":
    main()
