#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spotify 浏览器自动化添加歌曲脚本
使用 Playwright 操作 Spotify 网页版，无需 API
"""
import sys
import io
# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import csv
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError


class SpotifyBrowserAdder:
    """Spotify 浏览器添加器"""

    def __init__(self, headless: bool = False, slow_mo: int = 1000):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser = None
        self.context = None
        self.page: Page = None
        self.base_url = "https://open.spotify.com"

    def start_browser(self):
        """启动浏览器"""
        print("🌐 启动浏览器...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        print("✅ 浏览器启动成功")

    def login(self, wait_seconds: int = 180) -> bool:
        """登录 Spotify（用户手动登录）"""
        print(f"\n🔐 打开 Spotify 登录页面...")
        self.page.goto(f"{self.base_url}/login")
        print(f"⏳ 请在 {wait_seconds} 秒内手动登录 Spotify 账号")
        print("💡 提示：登录成功后，按回车继续，或等待自动检测")
        print("💡 建议：勾选'记住我'选项，下次可以自动登录")

        # 等待用户登录，检测是否跳转到主页
        for i in range(wait_seconds):
            current_url = self.page.url
            if "/login" not in current_url and "spotify.com" in current_url:
                print("✅ 检测到登录成功！")
                return True
            time.sleep(1)
            if i % 20 == 0 and i > 0:
                print(f"⏳ 已等待 {i} 秒...")

        print("❌ 登录超时")
        return False

    def add_song_to_liked(self, track_id: str, song_info: str = "") -> bool:
        """添加歌曲到已点赞"""
        try:
            # 直接访问歌曲页面
            track_url = f"{self.base_url}/track/{track_id}"
            self.page.goto(track_url)

            # 等待页面加载
            time.sleep(2)

            # 尝试多种方式找到点赞按钮
            like_button = None

            # 方式1: 通过 aria-label 查找（未点赞状态）
            for selector in [
                'button[aria-label="添加到已喜欢的内容"]',
                'button[aria-label="Save to Your Library"]',
                'button[aria-label="保存到你的音乐库"]',
                'button[aria-label="Add to Liked Songs"]',
                '[data-testid="add-button"]',
                'button[aria-label*="喜欢"]',
                'button[aria-label*="Like"]'
            ]:
                try:
                    like_button = self.page.wait_for_selector(selector, timeout=3000)
                    if like_button:
                        break
                except PlaywrightTimeoutError:
                    continue

            if like_button:
                # 检查是否已经点赞（aria-label 可能不同）
                aria_label = like_button.get_attribute("aria-label") or ""

                if "已添加" in aria_label or "已喜欢" in aria_label or "Saved" in aria_label or "Liked" in aria_label:
                    print(f"⏭️  歌曲已点赞: {song_info}")
                    return True

                # 点击点赞按钮
                like_button.click()
                time.sleep(1)
                print(f"❤️  已添加到已点赞: {song_info}")
                return True
            else:
                print(f"⚠️  未找到点赞按钮: {song_info}")
                return False

        except Exception as e:
            print(f"❌ 添加歌曲失败 {song_info}: {e}")
            return False

    def read_csv_file(self, csv_path: str) -> List[Dict]:
        """读取 CSV 文件"""
        print(f"\n📁 读取 CSV 文件: {csv_path}")

        if not os.path.exists(csv_path):
            print(f"❌ 错误: CSV 文件不存在: {csv_path}")
            return []

        songs = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    track_uri = row.get('Track URI', '').strip()
                    if track_uri and 'spotify:track:' in track_uri:
                        track_id = track_uri.replace('spotify:track:', '')
                        songs.append({
                            'track_id': track_id,
                            'track_name': row.get('Track Name', '').strip(),
                            'artist_name': row.get('Artist Name(s)', '').strip(),
                            'album_name': row.get('Album Name', '').strip()
                        })

            print(f"✅ 成功读取 {len(songs)} 首歌曲")
            return songs

        except Exception as e:
            print(f"❌ 读取 CSV 文件失败: {e}")
            return []

    def process_songs(self, songs: List[Dict], delay: int = 3) -> dict:
        """批量处理歌曲"""
        print(f"\n🎵 开始处理 {len(songs)} 首歌曲...")
        print(f"⏱️  每首歌间隔 {delay} 秒\n")

        success_count = 0
        fail_count = 0
        skip_count = 0

        for i, song in enumerate(songs, 1):
            song_info = f"{song['track_name']} - {song['artist_name']}"
            print(f"[{i}/{len(songs)}] 处理: {song_info}")

            result = self.add_song_to_liked(song['track_id'], song_info)

            if result is True:
                success_count += 1
            elif result is None:
                skip_count += 1
            else:
                fail_count += 1

            # 最后一首歌不需要等待
            if i < len(songs):
                time.sleep(delay)

        # 结果汇总
        print("\n" + "=" * 80)
        print("📊 处理结果")
        print("=" * 80)
        print(f"总歌曲数: {len(songs)}")
        print(f"成功添加: {success_count}")
        print(f"跳过: {skip_count}")
        print(f"失败: {fail_count}")
        print(f"成功率: {success_count/len(songs)*100:.1f}%" if len(songs) > 0 else "0%")
        print(f"🕒 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return {
            'total': len(songs),
            'success': success_count,
            'skip': skip_count,
            'fail': fail_count
        }

    def close(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("\n👋 浏览器已关闭")

    def run(self, csv_path: str, delay: int = 3):
        """运行主流程"""
        try:
            # 1. 启动浏览器
            self.start_browser()

            # 2. 登录
            if not self.login():
                return False

            # 3. 读取 CSV
            songs = self.read_csv_file(csv_path)
            if not songs:
                return False

            # 显示前3首
            print(f"\n📋 前3首歌曲示例:")
            for i, song in enumerate(songs[:3], 1):
                print(f"  {i}. {song['track_name']} - {song['artist_name']}")

            # 确认继续
            if len(songs) > 10:
                print(f"\n⚠️  准备处理 {len(songs)} 首歌曲，预计需要 {len(songs) * delay / 60:.1f} 分钟")
                input("按 Enter 键继续，或 Ctrl+C 取消...")

            # 4. 处理歌曲
            self.process_songs(songs, delay)

            return True

        except KeyboardInterrupt:
            print("\n\n⏹️  用户中断")
            return False
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            return False
        finally:
            self.close()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='Spotify 浏览器自动化添加歌曲')
    parser.add_argument('--csv', default='liked.csv', help='CSV 文件路径 (默认: liked.csv)')
    parser.add_argument('--delay', type=int, default=3, help='每首歌的间隔秒数 (默认: 3)')
    parser.add_argument('--headless', action='store_true', help='无头模式 (不显示浏览器窗口)')

    args = parser.parse_args()

    # 确定 CSV 文件路径
    csv_path = args.csv
    if not os.path.isabs(csv_path):
        script_dir = Path(__file__).parent
        csv_path = str(script_dir / csv_path)

    print(f"📁 CSV 文件路径: {csv_path}")

    if not os.path.exists(csv_path):
        print(f"❌ 错误: CSV 文件不存在: {csv_path}")
        return

    # 创建添加器
    adder = SpotifyBrowserAdder(headless=args.headless, slow_mo=500)

    # 运行
    success = adder.run(csv_path, args.delay)

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
