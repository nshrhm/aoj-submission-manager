#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AOJ Submission Ranking Generator
This script reads user submission data from user.csv and problem definitions from prob.csv,
calculates total score rankings and per-problem submission time rankings,
and outputs the results as TSV files.
"""

import csv
import os
from datetime import datetime

def convert_timestamp(ms):
    """
    Convert UNIX timestamp (milliseconds) to readable date string.
    @param ms: UNIX timestamp in milliseconds
    @return: Formatted string in 'YYYY/MM/DD HH:MM:SS' format or '未提出' if invalid
    """
    try:
        dt = datetime.fromtimestamp(int(ms) / 1000)
        return dt.strftime('%Y/%m/%d %H:%M:%S')
    except (ValueError, TypeError, OSError):
        return "未提出"

def read_user_data(filename):
    """
    Read user submission data from CSV file.
    All rows are treated as student data (no header).
    @param filename: Path to user.csv
    @return: List of user data rows
    """
    users = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            users.append(row)
    return None, users

def read_problem_ids(filename):
    """
    Read problem IDs from CSV file.
    @param filename: Path to prob.csv
    @return: List of problem IDs
    """
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return next(reader)  # First row contains problem IDs

def calculate_total_ranking(users):
    """
    Calculate ranking based on total score.
    Exclude users with total score of 0.
    For ties, sort by account name alphabetically.
    @param users: List of user data rows
    @return: Sorted list of (rank, total_score, account, surname, name)
    """
    rankings = []
    debug_log = []
    for user in users:
        account = user[3]  # D列: アカウント
        surname = user[1]  # B列: 姓
        name = user[2]     # C列: 名
        total_score = 0
        for i in range(4, len(user), 3):  # Score columns start at index 4, step by 3
            try:
                score = int(user[i])
                total_score += score
            except (ValueError, IndexError):
                continue
        if total_score > 0:
            rankings.append((total_score, account, surname, name))
            debug_log.append(f"Included: {account} ({surname} {name}), Total Score: {total_score}")
        else:
            debug_log.append(f"Excluded: {account} ({surname} {name}), Total Score: {total_score}")
    
    # Sort by total score descending, then by account name ascending for ties
    rankings.sort(key=lambda x: (-x[0], x[1]))
    result = []
    current_rank = 1
    current_score = None
    for i, (score, account, surname, name) in enumerate(rankings):
        if current_score is None or score != current_score:
            current_rank = i + 1
            current_score = score
        result.append((current_rank, score, account, surname, name))
    
    # Write debug log
    os.makedirs('rankings', exist_ok=True)
    with open('rankings/debug_log_total_ranking.txt', 'w', encoding='utf-8') as f:
        f.write("Total Ranking Debug Log\n")
        f.write("=======================\n")
        for log_entry in debug_log:
            f.write(log_entry + "\n")
        f.write("\nFinal Rankings:\n")
        for entry in result:
            f.write(f"Rank {entry[0]}: {entry[2]} ({entry[3]} {entry[4]}), Score: {entry[1]}\n")
    
    return result

def calculate_problem_ranking(users, problem_index, problem_id):
    """
    Calculate ranking for a specific problem based on submission time.
    Exclude users who haven't submitted (score=0 or invalid timestamp).
    @param users: List of user data rows
    @param problem_index: Index of the problem in prob.csv list
    @param problem_id: Problem ID for naming
    @return: Sorted list of (rank, submission_time_str, account, surname, name)
    """
    base_index = 4 + problem_index * 3  # Start index of problem data in user.csv
    rankings = []
    for user in users:
        account = user[3]
        surname = user[1]
        name = user[2]
        try:
            score = int(user[base_index])  # Score
            timestamp = int(user[base_index + 1])  # Submission timestamp
            if score > 0 and timestamp > 0:
                time_str = convert_timestamp(timestamp)
                rankings.append((timestamp, time_str, account, surname, name))
        except (ValueError, IndexError):
            continue
    
    rankings.sort()  # Sort by timestamp ascending
    result = []
    for rank, (_, time_str, account, surname, name) in enumerate(rankings, 1):
        result.append((rank, time_str, account, surname, name))
    return result

def write_tsv(filename, header, data):
    """
    Write ranking data to TSV file.
    @param filename: Output file path
    @param header: Header row for TSV
    @param data: List of data rows
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)
        for row in data:
            writer.writerow(row)

def main():
    """Main function to generate rankings."""
    user_file = 'user.csv'
    prob_file = 'prob.csv'
    output_dir = 'rankings'
    timestamp = datetime.now().strftime('%Y%m%d')
    
    # Read data
    _, users = read_user_data(user_file)
    problem_ids = read_problem_ids(prob_file)
    
    # Calculate and output total ranking
    total_ranking = calculate_total_ranking(users)
    total_header = ['順位', '全得点', 'AIZU ID', '姓', '名']
    write_tsv(f'{output_dir}/total_ranking_{timestamp}.tsv', total_header, total_ranking)
    
    # Calculate and output ranking for each problem
    for idx, problem_id in enumerate(problem_ids):
        problem_ranking = calculate_problem_ranking(users, idx, problem_id)
        problem_header = ['順位', problem_id, 'AIZU ID', '姓', '名']
        write_tsv(f'{output_dir}/{problem_id}_ranking_{timestamp}.tsv', problem_header, problem_ranking)

if __name__ == '__main__':
    main()
