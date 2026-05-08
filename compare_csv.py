#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较两个 Spotify CSV 文件，找出 liked.csv 中有但 My Spotify Library.csv 里没有的歌曲
"""
import sys
import io
# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import csv
from typing import Set, Dict


def get_track_ids(csv_path: str) -> Set[str]:
    """从 CSV 文件中提取所有 Track ID"""
    track_ids = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 支持两种格式的列名
            track_uri = row.get('Track URI', '').strip()
            spotify_id = row.get('Spotify - id', '').strip()

            if track_uri and 'spotify:track:' in track_uri:
                track_id = track_uri.replace('spotify:track:', '')
                track_ids.add(track_id)
            elif spotify_id:
                track_ids.add(spotify_id)
    return track_ids


def get_song_info(csv_path: str) -> Dict[str, Dict]:
    """从 CSV 文件中提取所有歌曲信息"""
    songs = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            track_uri = row.get('Track URI', '').strip()
            if track_uri and 'spotify:track:' in track_uri:
                track_id = track_uri.replace('spotify:track:', '')
                songs[track_id] = {
                    'Track URI': track_uri,
                    'Track Name': row.get('Track Name', '').strip(),
                    'Artist Name(s)': row.get('Artist Name(s)', '').strip(),
                    'Album Name': row.get('Album Name', '').strip()
                }
    return songs


def main():
    liked_file = 'liked.csv'
    library_file = 'result.csv'
    output_file = 'diff.csv'

    print(f"🔍 比较 {liked_file} 和 {library_file}...")

    # 获取两个文件的歌曲信息
    liked_songs = get_song_info(liked_file)
    library_ids = get_track_ids(library_file)

    print(f"✅ {liked_file}: {len(liked_songs)} 首歌曲")
    print(f"✅ {library_file}: {len(library_ids)} 首歌曲")

    # 找出只在 liked.csv 中的歌曲
    new_songs = []
    for track_id, song in liked_songs.items():
        if track_id not in library_ids:
            new_songs.append(song)

    print(f"\n📊 结果：{len(new_songs)} 首歌曲只存在于 {liked_file} 中")

    if not new_songs:
        print("🎉 所有歌曲都已在音乐库中")
        return

    # 导出到 temp.csv
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Track URI', 'Track Name', 'Artist Name(s)', 'Album Name'])
        writer.writeheader()
        writer.writerows(new_songs)

    print(f"💾 已导出到 {output_file}")

    # 显示前10首
    print("\n📋 前10首歌曲:")
    for i, song in enumerate(new_songs[:10], 1):
        print(f"  {i}. {song['Track Name']} - {song['Artist Name(s)']}")


if __name__ == "__main__":
    main()
