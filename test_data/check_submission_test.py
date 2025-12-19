#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file check_submission_test.py
@brief check_submission.pyのテストコード
"""

import unittest
import os
import csv
import shutil
from check_submission import get_max_info, normalize_submission_data, NO_SUBMISSION

class TestCheckSubmission(unittest.TestCase):
    def setUp(self):
        """テスト前の準備"""
        # テストデータのパス
        self.user_csv = "test_data/user_test.csv"
        self.prob_csv = "test_data/prob_test.csv"
        
        # バックアップ作成
        if os.path.exists(self.user_csv):
            shutil.copy(self.user_csv, f"{self.user_csv}.bak")
        if os.path.exists(self.prob_csv):
            shutil.copy(self.prob_csv, f"{self.prob_csv}.bak")

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # バックアップから復元
        if os.path.exists(f"{self.user_csv}.bak"):
            shutil.move(f"{self.user_csv}.bak", self.user_csv)
        if os.path.exists(f"{self.prob_csv}.bak"):
            shutil.move(f"{self.prob_csv}.bak", self.prob_csv)

    def test_get_max_info_normal(self):
        """get_max_info関数の正常系テスト"""
        # 既存のユーザーと問題で実行
        score, date, judge_id = get_max_info("test1", "ITP1_1_A")
        self.assertIsInstance(score, int)
        self.assertIsInstance(date, int)
        self.assertIsInstance(judge_id, int)
        self.assertGreaterEqual(score, 0)
        self.assertGreaterEqual(date, 0)
        self.assertGreaterEqual(judge_id, NO_SUBMISSION)

    def test_get_max_info_invalid_user(self):
        """存在しないユーザーでのテスト"""
        score, date, judge_id = get_max_info("invalid_user", "ITP1_1_A")
        self.assertEqual(score, 0)
        self.assertEqual(date, 0)
        self.assertEqual(judge_id, NO_SUBMISSION)

    def test_normalize_submission_data(self):
        """データ正規化のテスト"""
        # 正常なデータ
        row = ["123456", "テスト", "太郎", "test1", "100", "1683936000000", "12345"]
        result = normalize_submission_data(row, 1)
        self.assertEqual(len(result), 7)  # 基本情報4 + (スコア,日時,judgeId)×1
        self.assertEqual(result[4:], ["100", "1683936000000", "12345"])

        # 不正なデータ
        row = ["123456", "テスト", "太郎", "test1", "invalid", "-1", "abc"]
        result = normalize_submission_data(row, 1)
        self.assertEqual(result[4:], ["0", "0", str(NO_SUBMISSION)])

    def test_normalize_submission_missing_data(self):
        """データ不足時の正規化テスト"""
        row = ["123456", "テスト", "太郎", "test1"]
        result = normalize_submission_data(row, 1)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[4:], ["0", "0", str(NO_SUBMISSION)])

    def test_normalize_submission_invalid_score(self):
        """不正なスコアの正規化テスト"""
        # スコアが範囲外
        row = ["123456", "テスト", "太郎", "test1", "101", "1683936000000", "12345"]
        result = normalize_submission_data(row, 1)
        self.assertEqual(result[4], "0")

        # 負のスコア
        row = ["123456", "テスト", "太郎", "test1", "-50", "1683936000000", "12345"]
        result = normalize_submission_data(row, 1)
        self.assertEqual(result[4], "0")

    def test_normalize_submission_multiple_problems(self):
        """複数問題のデータ正規化テスト"""
        row = ["123456", "テスト", "太郎", "test1",
               "100", "1683936000000", "12345",
               "80", "1683936100000", "12346"]
        result = normalize_submission_data(row, 2)
        self.assertEqual(len(result), 10)  # 基本情報4 + (スコア,日時,judgeId)×2
        self.assertEqual(result[4:7], ["100", "1683936000000", "12345"])
        self.assertEqual(result[7:], ["80", "1683936100000", "12346"])

    def test_update_tracking(self):
        """更新情報の追跡テスト"""
        # テスト用にmain関数の一部を再現
        updated_entries = []
        
        # ケース1: スコアが上昇する場合
        cur_score_int = 80
        max_score = 100
        cur_date_int = 1683936000000
        max_date = 1683936100000
        uid = "test1"
        pid = "ITP1_1_A"
        
        if (max_score > cur_score_int or 
            (max_score == cur_score_int and max_date > cur_date_int)):
            updated_entries.append((uid, pid))
        
        self.assertEqual(len(updated_entries), 1)
        self.assertEqual(updated_entries[0], ("test1", "ITP1_1_A"))
        
        # ケース2: 同じスコアで日時が新しい場合
        cur_score_int = 100
        max_score = 100
        cur_date_int = 1683936000000
        max_date = 1683936100000
        uid = "test1"
        pid = "ITP1_1_B"
        
        if (max_score > cur_score_int or 
            (max_score == cur_score_int and max_date > cur_date_int)):
            updated_entries.append((uid, pid))
        
        self.assertEqual(len(updated_entries), 2)
        self.assertEqual(updated_entries[1], ("test1", "ITP1_1_B"))
        
        # ケース3: 更新が不要な場合
        cur_score_int = 100
        max_score = 80
        cur_date_int = 1683936100000
        max_date = 1683936000000
        uid = "test1"
        pid = "ITP1_1_C"
        
        if (max_score > cur_score_int or 
            (max_score == cur_score_int and max_date > cur_date_int)):
            updated_entries.append((uid, pid))
        
        self.assertEqual(len(updated_entries), 2)  # 更新されないことを確認

if __name__ == "__main__":
    unittest.main()
