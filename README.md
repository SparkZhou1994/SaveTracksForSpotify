# Spotify 歌单保存系统

将CSV文件中的歌曲保存到Spotify歌单。

## 📋 功能

- 读取CSV格式的歌曲记录
- 通过Spotify API创建歌单
- 添加歌曲到已点赞（我的最爱）
- 详细的API请求/响应日志
- 批量处理（支持大量歌曲）

## 📁 文件结构

```
spotify/
├── liked.csv              # 歌曲记录CSV文件
├── save_to_spotify.py     # 主脚本
├── .env.example           # 环境变量示例
└── README.md             # 本文件
```

## 🚀 快速开始

### 1. 准备环境

```bash
# 安装依赖
pip install requests

# 设置Spotify API凭证
cp .env.example .env
# 编辑 .env 文件，填入你的 Spotify Client ID 和 Secret
```

### 2. 获取Spotify API凭证

1. 访问 [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. 创建新应用
3. 获取 `Client ID` 和 `Client Secret`
4. 在应用设置中添加重定向URI（如果需要OAuth）

### 3. 运行脚本

```bash
# 设置环境变量
export SPOTIFY_CLIENT_ID="你的客户端ID"
export SPOTIFY_CLIENT_SECRET="你的客户端密钥"

# 运行脚本
python save_to_spotify.py --playlist "我的收藏" --add-to-liked
```

## 📊 CSV文件格式

CSV文件应包含以下列（Spotify导出格式）：
- `Track URI` - 歌曲URI (spotify:track:...)
- `Track Name` - 歌曲名称
- `Artist URI(s)` - 艺术家URI
- `Artist Name(s)` - 艺术家名称
- `Album URI` - 专辑URI
- `Album Name` - 专辑名称
- ... 其他字段可选

## 🎯 使用示例

### 示例1: 创建歌单并添加到已点赞
```bash
python save_to_spotify.py \
  --playlist "我的最爱歌曲" \
  --description "从CSV导入的收藏歌曲" \
  --add-to-liked
```

### 示例2: 只添加到已点赞（不创建歌单）
```bash
python save_to_spotify.py --add-to-liked
```

### 示例3: 指定不同的CSV文件
```bash
python save_to_spotify.py \
  --csv "my_songs.csv" \
  --playlist "自定义歌单"
```

### 示例4: 直接设置凭证
```bash
python save_to_spotify.py \
  --client-id "你的客户端ID" \
  --client-secret "你的客户端密钥" \
  --playlist "测试歌单"
```

## 🔧 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--csv` |  | CSV文件路径 | `liked.csv` |
| `--playlist` |  | 歌单名称 | （可选） |
| `--description` |  | 歌单描述 | 空 |
| `--add-to-liked` |  | 同时添加到已点赞 | `false` |
| `--client-id` |  | Spotify Client ID | 环境变量 |
| `--client-secret` |  | Spotify Client Secret | 环境变量 |

## 📝 脚本输出

脚本会显示详细的API请求和响应信息：

```
📤 API请求信息
========================================
方法: POST
URL: https://api.spotify.com/v1/users/{user_id}/playlists
请求头:
  Authorization: Bearer BQBP2C...（隐藏）
  Content-Type: application/json
请求数据:
{
  "name": "我的收藏",
  "description": "从CSV导入",
  "public": true
}

📥 API响应信息
========================================
状态码: 201
响应头:
  content-type: application/json; charset=utf-8
响应数据 (JSON):
{
  "id": "37i9dQZF1DXcBWIGoYBM5M",
  "name": "我的收藏",
  "external_urls": {
    "spotify": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
  }
}
```

## ⚠️ 注意事项

### 1. 认证限制
- `client_credentials` 认证只能访问公开数据
- 需要OAuth用户认证才能操作用户歌单
- 脚本当前使用client_credentials，可能需要修改为OAuth

### 2. API限制
- 速率限制: 每批次请求之间会有延迟
- 批量限制: 每次最多添加100首歌曲到歌单
- 每日限制: Spotify API有每日调用限制

### 3. 权限范围
需要的Spotify API权限范围：
- `playlist-modify-public` (创建公开歌单)
- `playlist-modify-private` (创建私密歌单)
- `user-library-modify` (修改已点赞歌曲)

### 4. 错误处理
- 脚本会捕获并显示错误信息
- 失败的批次会记录但继续处理
- 建议先使用少量歌曲测试

## 🔄 处理流程

1. **认证** → 获取访问令牌
2. **用户信息** → 获取当前用户ID
3. **读取CSV** → 解析歌曲记录
4. **提取URI** → 获取所有track URI
5. **创建歌单** → 创建新歌单（如需要）
6. **添加歌曲** → 批量添加歌曲到歌单
7. **添加到已点赞** → 添加到我的最爱（如需要）

## 🐛 故障排除

### 常见问题1: 认证失败
```
❌ 认证失败: 401
```
**解决方案:**
- 检查Client ID和Secret是否正确
- 确保在Spotify Dashboard中应用状态为"Active"

### 常见问题2: 用户信息获取失败
```
❌ 获取用户信息失败: 403
```
**解决方案:**
- client_credentials认证无法获取用户信息
- 需要实现OAuth用户认证流程

### 常见问题3: CSV解析失败
```
❌ 解析CSV文件失败
```
**解决方案:**
- 检查CSV文件格式和编码
- 确保文件包含必要的列
- 使用UTF-8编码保存文件

### 常见问题4: API速率限制
```
❌ 请求被限制: 429
```
**解决方案:**
- 增加批次间的延迟时间
- 减少每批次的歌曲数量
- 等待一段时间后重试

## 📈 性能优化

### 批量处理
- 每批次处理100首歌曲（歌单添加）
- 每批次处理50首歌曲（已点赞添加）
- 批次间延迟1秒避免速率限制

### 内存优化
- 流式读取CSV文件
- 分批处理歌曲URI
- 及时释放不需要的数据

### 错误恢复
- 批次失败不影响其他批次
- 记录失败的具体原因
- 提供重试机制

## 🔮 未来改进

### 计划功能
- [ ] OAuth用户认证支持
- [ ] 进度条显示
- [ ] 断点续传
- [ ] 多线程处理
- [ ] 错误自动重试

### 集成选项
- [ ] Docker容器化
- [ ] Web界面
- [ ] 定时任务
- [ ] 多平台支持

## 📄 许可证

MIT License

## 🙏 致谢

- [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- Spotify开发者社区
- 所有贡献者

## 🆘 获取帮助

如有问题，请：
1. 检查错误日志
2. 查看Spotify API文档
3. 在GitHub创建Issue
4. 联系开发者

---

**开始使用:**
```bash
# 1. 设置环境变量
export SPOTIFY_CLIENT_ID="你的ID"
export SPOTIFY_CLIENT_SECRET="你的密钥"

# 2. 运行脚本
python save_to_spotify.py --playlist "我的歌单" --add-to-liked
```