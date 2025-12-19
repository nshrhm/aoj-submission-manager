import requests
import json
import os
from datetime import datetime

class AOJSubmissionDownloader:
    """
    Aizu Online Judge (AOJ) の提出プログラムをダウンロードするためのクラス

    指定したユーザーIDと問題IDに対して、最高得点のPython提出を取得し、
    ローカルのdownloadsディレクトリに保存します。
    """

    def __init__(self):
        # AOJのAPIエンドポイント
        self.judge_api = 'https://judgeapi.u-aizu.ac.jp'
        # AOJのWebサイトエンドポイント（未使用だが将来の拡張用に保持）
        self.web_endpoint = 'https://onlinejudge.u-aizu.ac.jp'
        # 提出ステータスのマッピング（数値コード→文字列）
        self.status_map = {
            0: 'Compile Error',
            1: 'Wrong Answer',
            2: 'Time Limit Exceeded',
            3: 'Memory Limit Exceeded',
            4: 'Accepted',
            5: 'Waiting',
            6: 'Output Limit Exceeded',
            7: 'Runtime Error',
            8: 'Presentation Error',
            9: 'Running'
        }
        
    def get_submission_records(self, user_id: str, problem_id: str, page: int = 0, size: int = 100) -> list:
        """
        指定ユーザーと問題の提出記録をAOJ APIから取得する

        @param user_id AOJのユーザーID
        @param problem_id AOJの問題ID
        @param page ページ番号（デフォルト0）
        @param size 1ページあたりの取得件数（デフォルト100）
        @return 提出記録のリスト（取得失敗時はNone）
        """
        url = f"{self.judge_api}/submission_records/users/{user_id}/problems/{problem_id}"
        params = {'page': page, 'size': size}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return None

    def get_source_code(self, submission_id: int) -> dict:
        """
        指定した提出IDのソースコードをAOJ APIから取得する

        @param submission_id 提出ID（judgeId）
        @return ソースコード情報の辞書（取得失敗時はNone）
        """
        url = f"{self.judge_api}/reviews/{submission_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def download_best_python_submission(self, user_id: str, problem_id: str) -> bool:
        """
        指定ユーザー・問題の最高得点Python提出をダウンロードし、ファイル保存する

        @param user_id AOJのユーザーID
        @param problem_id AOJの問題ID
        @return ダウンロード成功ならTrue、失敗ならFalse
        """
        submissions = self.get_submission_records(user_id, problem_id)
        if not submissions:
            print(f"ユーザー {user_id} の問題 {problem_id} に提出が見つかりません。")
            return False

        # Python言語の提出のみ抽出
        python_submissions = [s for s in submissions if s['language'] in ['Python', 'Python3']]
        if not python_submissions:
            print(f"ユーザー {user_id} の問題 {problem_id} にPython提出が見つかりません。")
            return False

        # 最高スコアの提出を選択
        best_submission = max(python_submissions, key=lambda s: s.get('score', 0))
        submission_id = best_submission['judgeId']
        status = self.status_map.get(best_submission['status'], 'Unknown')
        score = best_submission.get('score', 0)
        
        # ソースコードを取得
        submission_data = self.get_source_code(submission_id)
        if not submission_data:
            print(f"提出ID {submission_id} のソースコードを取得できませんでした。")
            return False

        # downloadsディレクトリがなければ作成
        os.makedirs("downloads", exist_ok=True)
            
        # ファイル名を作成し、ソースコードを書き込み
        filename = f"downloads/{problem_id}_score{score}.py"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(submission_data["sourceCode"])
        
        print(f"最高得点のPython提出 (スコア: {score}, ステータス: {status}) を {filename} に保存しました。")
        return True

def main():
    """
    コマンドラインからユーザーIDと問題IDを入力し、
    最高得点のPython提出をダウンロードする処理を実行する。
    """
    downloader = AOJSubmissionDownloader()
    
    # ユーザーから入力を受け取る
    user_id = input("ユーザーIDを入力してください: ")
    problem_id = input("問題IDを入力してください（例: ITP1_1_A）: ")
    
    downloader.download_best_python_submission(user_id, problem_id)

if __name__ == "__main__":
    main()
