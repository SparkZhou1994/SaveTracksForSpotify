# Spotify 歌曲添加工具

两种方式将 CSV 中的歌曲添加到 Spotify 已喜欢的内容：

## 📋 目录

1. [方式一：浏览器自动化（推荐）](#方式一浏览器自动化推荐)
2. [方式二：Spotify Web API（需Premium）](#方式二spotify-web-api需premium)
3. [CSV 文件格式](#csv-文件格式)
4. [常见问题](#常见问题)

---

## 方式一：浏览器自动化（推荐）

**优点：**
- ✅ 无需 Spotify Premium 账号
- ✅ 无需创建开发者应用
- ✅ 无需配置 Client ID/Secret
- ✅ 使用真实浏览器操作，稳定可靠

**缺点：**
- ⏱️ 需要手动登录一次
- ⏱️ 处理速度较慢（每首歌约3-5秒）

### 1. 安装依赖

```bash
# 激活虚拟环境
source spotify-env/Scripts/activate  # Windows (Git Bash)
# source spotify-env/bin/activate   # Linux/Mac

# 安装依赖
uv pip install playwright
python -m playwright install chromium
```

### 2. 使用方法

```bash
# 测试（小样本）
python browser_spotify.py --csv liked.csv --delay 5

# 完整导入（612首歌）
python browser_spotify.py --csv sorted.csv --delay 3

# 参数说明
--csv CSV_FILE    CSV 文件路径
--delay SECONDS   每首歌的间隔秒数（默认3秒）
--headless        无头模式（不显示浏览器窗口）
```

### 3. 操作流程

1. 运行脚本后，浏览器会自动打开
2. **在180秒内手动登录 Spotify 账号**（建议勾选"记住我"）
3. 登录成功后，脚本会自动开始处理
4. 控制台显示实时进度和统计

---

## 方式二：Spotify Web API（需Premium）

**注意：** 2025年起，Spotify 要求开发者账号必须有 **Premium 订阅** 才能使用此方式。如果没有 Premium，请使用方式一。

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```env
# Spotify Developer Dashboard 获取
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

# 可选配置
PLAYLIST_NAME=我的收藏
PLAYLIST_DESCRIPTION=从CSV导入的歌曲
ADD_TO_LIKED=true
```

### 2. 使用方法

```bash
source spotify-env/Scripts/activate
python save_to_spotify.py --csv liked.csv --playlist "我的收藏"
```

---

## CSV 文件格式

CSV 文件必须包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| Track URI | Spotify 歌曲 URI | spotify:track:1G391cbiT3v3Cywg8T7DM1 |
| Track Name | 歌曲名称 | Scar Tissue |
| Artist Name(s) | 艺术家名称 | Red Hot Chili Peppers |
| Album Name | 专辑名称 | Californication (Deluxe Edition) |

**示例：**
```csv
Track URI,Track Name,Artist Name(s),Album Name,Album Release Date
spotify:track:1G391cbiT3v3Cywg8T7DM1,Scar Tissue,Red Hot Chili Peppers,Californication (Deluxe Edition),1999-06-08
```

---

## 常见问题

### Q: 浏览器自动化会被封号吗？
A: 只要设置合理的延迟时间（3-5秒/首歌），模拟真实用户操作，风险极低。

### Q: 如何导出我现有的 Spotify 歌单？
A: 可以使用 [Exportify](https://exportify.net/) 或其他第三方工具导出为 CSV。

### Q: 612首歌需要多长时间？
A: 按每首歌3秒计算，大约需要 30 分钟。可以同时做其他事情，脚本后台自动运行。

### Q: 可以中断后继续吗？
A: 目前版本不支持断点续传，但已点赞的歌曲会被自动跳过，不会重复添加。

---

## 项目结构

```
spotify/
├── browser_spotify.py    # 浏览器自动化脚本（推荐）
├── save_to_spotify.py    # Spotify API 脚本
├── liked.csv             # 小样本测试数据
├── sorted.csv            # 完整歌曲数据（612首）
├── .env.example          # 环境变量模板
├── spotify-env/          # Python 虚拟环境
└── README.md             # 本文档
```
