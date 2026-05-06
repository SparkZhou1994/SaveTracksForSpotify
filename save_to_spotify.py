#!/usr/bin/env python3
"""
Spotify歌单保存脚本
读取CSV文件并通过Spotify API保存到Spotify歌单
"""

import os
import sys
from dotenv import load_dotenv
import json
import csv
import base64
import requests
import time
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse


def load_environment():
    """加载环境变量配置"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ 已加载环境配置: {env_path}")
    else:
        print("⚠️  未找到.env文件，将使用系统环境变量")


class SpotifyPlaylistSaver:
    """Spotify歌单保存器"""

    def __init__(self, client_id: str = None, client_secret: str = None, redirect_uri: str = None):
        self.client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.api_base = "https://api.spotify.com/v1"
        self.auth_code = None
        
    def print_request_info(self, method: str, url: str, headers: Dict = None, data: Any = None):
        """打印请求参数信息"""
        print("\n" + "=" * 80)
        print("📤 API请求信息")
        print("=" * 80)
        print(f"方法: {method}")
        print(f"URL: {url}")
        
        if headers:
            safe_headers = headers.copy()
            if 'Authorization' in safe_headers:
                # 隐藏完整的token，只显示前20个字符
                auth_header = safe_headers['Authorization']
                if len(auth_header) > 30:
                    safe_headers['Authorization'] = auth_header[:30] + "..."
            print("请求头:")
            for key, value in safe_headers.items():
                print(f"  {key}: {value}")
        
        if data:
            print("请求数据:")
            if isinstance(data, dict):
                print(json.dumps(data, indent=2, ensure_ascii=False))
            elif isinstance(data, str):
                try:
                    parsed = json.loads(data)
                    print(json.dumps(parsed, indent=2, ensure_ascii=False))
                except:
                    print(data[:200] + "..." if len(data) > 200 else data)
            else:
                print(str(data)[:200] + "..." if len(str(data)) > 200 else str(data))
        
        print("=" * 80)
    
    def print_response_info(self, response: requests.Response):
        """打印响应信息"""
        print("\n" + "=" * 80)
        print("📥 API响应信息")
        print("=" * 80)
        print(f"状态码: {response.status_code}")
        print(f"响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                response_data = response.json()
                print("响应数据 (JSON):")
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
            else:
                print(f"响应数据 (原始): {response.text[:500]}...")
        except:
            print(f"响应数据 (原始): {response.text[:500]}...")
        
        print("=" * 80)
    
    def refresh_access_token(self) -> bool:
        """使用刷新令牌获取新的访问令牌"""
        if not self.refresh_token:
            print("❌ 错误: 没有刷新令牌，需要重新认证")
            return False

        print("🔄 刷新访问令牌...")

        token_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        try:
            response = requests.post(token_url, headers=headers, data=data)

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                # 更新刷新令牌（如果返回）
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data.get("refresh_token")
                print("✅ 访问令牌刷新成功")
                return True
            else:
                print(f"❌ 刷新令牌失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 刷新令牌请求失败: {e}")
            return False

    def authenticate(self) -> bool:
        """使用OAuth 2.0授权码流程获取访问令牌"""
        print("🔐 开始Spotify API认证...")

        if not self.client_id:
            print("❌ 错误: 需要设置SPOTIFY_CLIENT_ID环境变量")
            print("💡 提示: 在 https://developer.spotify.com/dashboard 创建应用获取")
            return False

        if not self.client_secret:
            print("❌ 错误: 需要设置SPOTIFY_CLIENT_SECRET环境变量")
            return False

        # 1. 构建授权URL
        scopes = "playlist-modify-public playlist-modify-private user-library-modify user-read-private user-read-email"
        auth_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": scopes,
            "show_dialog": "true"
        }

        auth_url = f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(auth_params)}"

        print(f"\n🔗 请访问以下URL进行授权:")
        print(f"   {auth_url}")
        print(f"\n💡 授权后会跳转到本地地址，复制地址栏中的code参数值")

        # 尝试自动打开浏览器
        try:
            webbrowser.open(auth_url)
            print(f"✅ 浏览器已自动打开，请完成授权")
        except:
            print(f"⚠️  无法自动打开浏览器，请手动访问上述URL")

        # 2. 获取授权码
        auth_code = input("\n请输入授权码(code): ").strip()

        if not auth_code:
            print("❌ 错误: 授权码不能为空")
            return False

        # 3. 交换访问令牌
        token_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri
        }

        # 打印请求信息
        self.print_request_info("POST", token_url, headers, {k: v for k, v in data.items() if k != 'code'})

        try:
            response = requests.post(token_url, headers=headers, data=data)

            # 打印响应信息
            self.print_response_info(response)

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                print("✅ Spotify API认证成功")
                print(f"   令牌类型: {token_data.get('token_type')}")
                print(f"   过期时间: {token_data.get('expires_in')}秒")
                print(f"   权限范围: {token_data.get('scope')}")
                return True
            else:
                print(f"❌ 认证失败: {response.status_code}")
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                if error_data.get('error'):
                    print(f"   错误信息: {error_data.get('error_description', error_data.get('error'))}")
                return False

        except Exception as e:
            print(f"❌ 认证请求失败: {e}")
            return False
    
    def get_current_user(self) -> Optional[str]:
        """获取当前用户ID（需要用户认证）"""
        print("\n👤 获取当前用户信息...")
        
        if not self.access_token:
            print("❌ 错误: 需要先认证获取访问令牌")
            return None
        
        url = f"{self.api_base}/me"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # 打印请求信息
        self.print_request_info("GET", url, headers)
        
        try:
            response = requests.get(url, headers=headers)
            
            # 打印响应信息
            self.print_response_info(response)
            
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data.get("id")
                display_name = user_data.get("display_name", "未知用户")
                email = user_data.get("email", "未知邮箱")
                
                print(f"✅ 获取用户信息成功")
                print(f"   用户ID: {self.user_id}")
                print(f"   显示名: {display_name}")
                print(f"   邮箱: {email}")
                print(f"   国家: {user_data.get('country', '未知')}")
                print(f"   产品类型: {user_data.get('product', '未知')}")
                
                return self.user_id
            else:
                print(f"❌ 获取用户信息失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取用户信息失败: {e}")
            return None
    
    def read_csv_file(self, csv_path: str) -> List[Dict]:
        """读取CSV文件"""
        print(f"\n📁 读取CSV文件: {csv_path}")
        
        if not os.path.exists(csv_path):
            print(f"❌ 错误: CSV文件不存在: {csv_path}")
            return []
        
        songs = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # 使用csv模块读取，处理引号和特殊字符
                reader = csv.DictReader(f)
                
                # 检查文件是否有数据
                fieldnames = reader.fieldnames
                if not fieldnames:
                    print("❌ 错误: CSV文件没有标题行")
                    return []
                
                print(f"📊 CSV文件字段: {', '.join(fieldnames)}")
                
                for i, row in enumerate(reader, 1):
                    try:
                        song = self.parse_csv_row(row)
                        songs.append(song)
                        
                        if i <= 3:  # 显示前3条记录作为示例
                            print(f"  记录{i}: {song['track_name']} - {song['artist_name']}")
                        
                    except Exception as e:
                        print(f"⚠️  解析第{i}行失败: {e}")
                        continue
                
                print(f"✅ 成功读取 {len(songs)} 首歌曲")
                
        except Exception as e:
            print(f"❌ 读取CSV文件失败: {e}")
            return []
        
        return songs
    
    def parse_csv_row(self, row: Dict) -> Dict[str, Any]:
        """解析CSV行数据"""
        # 根据你的CSV格式解析
        song = {
            'track_uri': row.get('Track URI', '').strip(),
            'track_name': row.get('Track Name', '').strip(),
            'artist_uri': row.get('Artist URI(s)', '').strip(),
            'artist_name': row.get('Artist Name(s)', '').strip(),
            'album_uri': row.get('Album URI', '').strip(),
            'album_name': row.get('Album Name', '').strip(),
            'album_artist_uri': row.get('Album Artist URI(s)', '').strip(),
            'album_artist_name': row.get('Album Artist Name(s)', '').strip(),
            'release_date': row.get('Album Release Date', '').strip(),
            'album_image_url': row.get('Album Image URL', '').strip(),
            'disc_number': int(row.get('Disc Number', 0)) if row.get('Disc Number') else 0,
            'track_number': int(row.get('Track Number', 0)) if row.get('Track Number') else 0,
            'duration_ms': int(row.get('Track Duration (ms)', 0)) if row.get('Track Duration (ms)') else 0,
            'preview_url': row.get('Track Preview URL', '').strip(),
            'explicit': row.get('Explicit', '').lower() == 'true',
            'popularity': int(row.get('Popularity', 0)) if row.get('Popularity') else 0,
            'isrc': row.get('ISRC', '').strip(),
            'added_by': row.get('Added By', '').strip(),
            'added_at': row.get('Added At', '').strip()
        }
        
        # 提取ID
        if song['track_uri'] and 'spotify:track:' in song['track_uri']:
            song['track_id'] = song['track_uri'].replace('spotify:track:', '')
        else:
            song['track_id'] = ''
        
        if song['artist_uri'] and 'spotify:artist:' in song['artist_uri']:
            song['artist_id'] = song['artist_uri'].replace('spotify:artist:', '')
        else:
            song['artist_id'] = ''
        
        if song['album_uri'] and 'spotify:album:' in song['album_uri']:
            song['album_id'] = song['album_uri'].replace('spotify:album:', '')
        else:
            song['album_id'] = ''
        
        return song
    
    def create_playlist(self, name: str, description: str = "", public: bool = True) -> Optional[str]:
        """创建歌单"""
        print(f"\n📋 创建歌单: {name}")
        
        if not self.user_id:
            print("❌ 错误: 需要先获取用户ID")
            return None
        
        if not self.access_token:
            print("❌ 错误: 需要先认证")
            return None
        
        url = f"{self.api_base}/users/{self.user_id}/playlists"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "name": name,
            "description": description,
            "public": public
        }
        
        # 打印请求信息
        self.print_request_info("POST", url, headers, data)
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # 打印响应信息
            self.print_response_info(response)
            
            if response.status_code == 201:
                playlist_data = response.json()
                playlist_id = playlist_data.get("id")
                playlist_name = playlist_data.get("name")
                playlist_url = playlist_data.get("external_urls", {}).get("spotify")
                tracks_total = playlist_data.get("tracks", {}).get("total", 0)
                
                print(f"✅ 歌单创建成功")
                print(f"   歌单ID: {playlist_id}")
                print(f"   歌单名: {playlist_name}")
                print(f"   公开性: {'公开' if playlist_data.get('public') else '私密'}")
                print(f"   歌曲数: {tracks_total}")
                print(f"   歌单链接: {playlist_url}")
                
                return playlist_id
            else:
                print(f"❌ 创建歌单失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 创建歌单失败: {e}")
            return None
    
    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> bool:
        """添加歌曲到歌单"""
        print(f"\n➕ 添加歌曲到歌单...")
        
        if not self.access_token:
            print("❌ 错误: 需要先认证")
            return False
        
        if not track_uris:
            print("⚠️  警告: 没有可添加的歌曲URI")
            return False
        
        url = f"{self.api_base}/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Spotify API一次最多添加100首歌曲
        total_songs = len(track_uris)
        success_count = 0
        fail_count = 0
        
        for i in range(0, total_songs, 100):
            batch = track_uris[i:i+100]
            batch_num = i // 100 + 1
            total_batches = (total_songs + 99) // 100
            
            print(f"\n📦 批次 {batch_num}/{total_batches}: 添加 {len(batch)} 首歌曲")
            
            data = {
                "uris": batch,
                "position": i  # 从指定位置开始添加
            }
            
            # 打印请求信息
            self.print_request_info("POST", url, headers, data)
            
            try:
                response = requests.post(url, headers=headers, json=data)
                
                # 打印响应信息
                self.print_response_info(response)
                
                if response.status_code == 201:
                    success_count += len(batch)
                    print(f"✅ 批次 {batch_num} 添加成功")
                    
                    # 显示批次中的部分歌曲
                    print(f"   本批次歌曲示例:")
                    for j, uri in enumerate(batch[:3], 1):
                        print(f"     {j}. {uri}")
                    if len(batch) > 3:
                        print(f"     ... 还有 {len(batch)-3} 首")
                        
                else:
                    fail_count += len(batch)
                    print(f"❌ 批次 {batch_num} 添加失败: {response.status_code}")
                    
            except Exception as e:
                fail_count += len(batch)
                print(f"❌ 批次 {batch_num} 添加失败: {e}")
            
            # 批次间延迟，避免速率限制
            if i + 100 < total_songs:
                print(f"⏳ 等待1秒后继续下一批次...")
                time.sleep(1)
        
        # 结果汇总
        print("\n" + "=" * 80)
        print("📊 添加歌曲结果")
        print("=" * 80)
        print(f"总歌曲数: {total_songs}")
        print(f"成功添加: {success_count}")
        print(f"失败: {fail_count}")
        print(f"成功率: {success_count/total_songs*100:.1f}%" if total_songs > 0 else "0%")
        print("=" * 80)
        
        return success_count > 0
    
    def save_to_liked_songs(self, track_uris: List[str]) -> bool:
        """保存到已点赞的歌曲（我的最爱）"""
        print(f"\n❤️  添加到已点赞的歌曲...")
        
        if not self.access_token:
            print("❌ 错误: 需要先认证")
            return False
        
        if not track_uris:
            print("⚠️  警告: 没有可添加的歌曲URI")
            return False
        
        # 提取track IDs
        track_ids = []
        for uri in track_uris:
            if uri.startswith('spotify:track:'):
                track_id = uri.replace('spotify:track:', '')
                track_ids.append(track_id)
        
        if not track_ids:
            print("❌ 错误: 没有有效的track ID")
            return False
        
        # Spotify API一次最多添加50首歌曲到已点赞
        total_songs = len(track_ids)
        success_count = 0
        fail_count = 0
        
        for i in range(0, total_songs, 50):
            batch = track_ids[i:i+50]
            batch_num = i // 50 + 1
            total_batches = (total_songs + 49) // 50
            
            print(f"\n📦 批次 {batch_num}/{total_batches}: 添加 {len(batch)} 首歌曲到已点赞")
            
            url = f"{self.api_base}/me/tracks"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "ids": batch
            }
            
            # 打印请求信息
            self.print_request_info("PUT", url, headers, data)
            
            try:
                response = requests.put(url, headers=headers, json=data)
                
                # 打印响应信息
                self.print_response_info(response)
                
                if response.status_code == 200:
                    success_count += len(batch)
                    print(f"✅ 批次 {batch_num} 添加到已点赞成功")
                else:
                    fail_count += len(batch)
                    print(f"❌ 批次 {batch_num} 添加到已点赞失败: {response.status_code}")
                    
            except Exception as e:
                fail_count += len(batch)
                print(f"❌ 批次 {batch_num} 添加到已点赞失败: {e}")
            
            # 批次间延迟
            if i + 50 < total_songs:
                print(f"⏳ 等待1秒后继续下一批次...")
                time.sleep(1)
        
        # 结果汇总
        print("\n" + "=" * 80)
        print("📊 添加到已点赞结果")
        print("=" * 80)
        print(f"总歌曲数: {total_songs}")
        print(f"成功添加: {success_count}")
        print(f"失败: {fail_count}")
        print(f"成功率: {success_count/total_songs*100:.1f}%" if total_songs > 0 else "0%")
        print("=" * 80)
        
        return success_count > 0
    
    def create_playlist_from_csv(self, csv_path: str, playlist_name: str = None, 
                               playlist_description: str = "", add_to_liked: bool = False) -> bool:
        """从CSV文件创建歌单"""
        print("=" * 80)
        print("🎵 Spotify 歌单创建器")
        print("=" * 80)
        
        # 1. 认证
        print("\n步骤1: Spotify API认证")
        if not self.authenticate():
            return False
        
        # 2. 获取用户ID（需要用户范围的认证）
        print("\n步骤2: 获取用户信息")
        user_id = self.get_current_user()
        if not user_id:
            print("⚠️  注意: client_credentials认证无法获取用户信息")
            print("⚠️  需要OAuth用户认证才能创建用户歌单")
            print("\n💡 解决方案:")
            print("1. 使用OAuth 2.0授权码流程")
            print("2. 或创建不需要用户上下文的公开歌单")
            return False
        
        # 3. 读取CSV文件
        print("\n步骤3: 读取CSV文件")
        songs = self.read_csv_file(csv_path)
        if not songs:
            print("❌ 错误: 没有读取到歌曲数据")
            return False
        
        # 显示歌曲摘要
        print(f"\n📋 歌曲摘要:")
        print(f"   总歌曲数: {len(songs)}")
        print(f"   示例歌曲:")
        for i, song in enumerate(songs[:5], 1):
            print(f"     {i}. {song['track_name']} - {song['artist_name']}")
        if len(songs) > 5:
            print(f"     ... 还有 {len(songs)-5} 首歌曲")
        
        # 4. 提取track URIs
        track_uris = [song['track_uri'] for song in songs if song.get('track_uri')]
        print(f"\n🎵 提取到 {len(track_uris)} 个有效的歌曲URI")
        
        if not track_uris:
            print("❌ 错误: 没有有效的歌曲URI")
            return False
        
        # 5. 添加到已点赞的歌曲
        if add_to_liked:
            print("\n❤️  步骤4: 添加到已点赞的歌曲")
            if not self.save_to_liked_songs(track_uris):
                print("⚠️  添加到已点赞失败，继续创建歌单...")
        
        # 6. 创建歌单
        if playlist_name:
            print(f"\n📋 步骤5: 创建歌单 '{playlist_name}'")
            playlist_id = self.create_playlist(playlist_name, playlist_description)
            
            if not playlist_id:
                print("❌ 错误: 创建歌单失败")
                return False
            
            # 7. 添加歌曲到歌单
            print(f"\n➕ 步骤6: 添加歌曲到歌单")
            if not self.add_tracks_to_playlist(playlist_id, track_uris):
                print("⚠️  添加歌曲到歌单失败")
                return False
        
        print("\n" + "=" * 80)
        print("🎉 任务完成!")
        print("=" * 80)
        
        if playlist_name:
            print(f"✅ 歌单 '{playlist_name}' 创建完成")
        if add_to_liked:
            print(f"✅ 歌曲已添加到已点赞")
        
        print(f"📊 总处理歌曲: {len(songs)} 首")
        print(f"🕒 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True

def main():
    """命令行入口"""
    load_environment()

    parser = argparse.ArgumentParser(description='Spotify歌单保存脚本')
    parser.add_argument('--csv', default='liked.csv', help='CSV文件路径 (默认: liked.csv)')
    parser.add_argument('--playlist', help='歌单名称 (如果不指定，只添加到已点赞)')
    parser.add_argument('--description', default='', help='歌单描述')
    parser.add_argument('--add-to-liked', action='store_true', help='同时添加到已点赞的歌曲')
    parser.add_argument('--client-id', help='Spotify Client ID (或设置SPOTIFY_CLIENT_ID环境变量)')
    parser.add_argument('--client-secret', help='Spotify Client Secret (或设置SPOTIFY_CLIENT_SECRET环境变量)')
    parser.add_argument('--redirect-uri', help='Spotify重定向URI (或设置SPOTIFY_REDIRECT_URI环境变量，默认: http://localhost:8888/callback)')
    
    args = parser.parse_args()
    
    # 确定CSV文件路径
    csv_path = args.csv
    if not os.path.isabs(csv_path):
        # 相对路径，相对于脚本目录
        script_dir = Path(__file__).parent
        csv_path = str(script_dir / csv_path)
    
    print(f"📁 CSV文件路径: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"❌ 错误: CSV文件不存在: {csv_path}")
        print(f"💡 请确保文件存在或使用 --csv 参数指定正确路径")
        return
    
    # 创建保存器
    saver = SpotifyPlaylistSaver(args.client_id, args.client_secret, args.redirect_uri)
    
    # 运行
    success = saver.create_playlist_from_csv(
        csv_path=csv_path,
        playlist_name=args.playlist,
        playlist_description=args.description,
        add_to_liked=args.add_to_liked
    )
    
    if not success:
        print("\n❌ 歌单保存失败")
        print("\n💡 常见问题和解决方案:")
        print("1. 认证失败:")
        print("   - 检查SPOTIFY_CLIENT_ID和SPOTIFY_CLIENT_SECRET环境变量")
        print("   - 在 https://developer.spotify.com/dashboard 创建应用")
        print("2. 用户信息获取失败:")
        print("   - client_credentials认证无法获取用户信息")
        print("   - 需要OAuth用户认证流程")
        print("3. API限制:")
        print("   - Spotify API有速率限制，请稍后重试")
        print("4. CSV文件格式:")
        print("   - 确保CSV文件格式正确，包含Track URI字段")
        sys.exit(1)

if __name__ == "__main__":
    main()