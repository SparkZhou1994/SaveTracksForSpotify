#!/bin/bash
# Spotify歌单保存 - 运行脚本

set -e

echo "=" * 60
echo "🎵 Spotify 歌单保存系统"
echo "=" * 60

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3"
    exit 1
fi

# 检查依赖
echo "🔍 检查Python依赖..."
python3 -c "
import importlib
deps = ['requests', 'csv', 'json', 'os', 'sys', 'argparse']
missing = []

for dep in deps:
    try:
        importlib.import_module(dep)
    except ImportError as e:
        missing.append(dep)

if missing:
    print(f'❌ 缺少依赖: {missing}')
    print('请运行: pip install requests')
    exit(1)
else:
    print('✅ 所有依赖都可用')
"

# 检查环境变量
echo -e "\n🔐 检查Spotify API凭证..."
if [[ -z "$SPOTIFY_CLIENT_ID" ]]; then
    echo "⚠️  警告: SPOTIFY_CLIENT_ID 环境变量未设置"
    echo "💡 设置方法: export SPOTIFY_CLIENT_ID='你的客户端ID'"
fi

if [[ -z "$SPOTIFY_CLIENT_SECRET" ]]; then
    echo "⚠️  警告: SPOTIFY_CLIENT_SECRET 环境变量未设置"
    echo "💡 设置方法: export SPOTIFY_CLIENT_SECRET='你的客户端密钥'"
fi

if [[ -z "$SPOTIFY_CLIENT_ID" || -z "$SPOTIFY_CLIENT_SECRET" ]]; then
    echo -e "\n📝 你可以创建 .env 文件:"
    echo "SPOTIFY_CLIENT_ID=你的客户端ID"
    echo "SPOTIFY_CLIENT_SECRET=你的客户端密钥"
    echo ""
    echo "然后运行: source .env"
fi

# 检查CSV文件
CSV_FILE="liked.csv"
echo -e "\n📁 检查CSV文件..."
if [[ -f "$CSV_FILE" ]]; then
    line_count=$(wc -l < "$CSV_FILE" || echo "0")
    echo "✅ 找到CSV文件: $CSV_FILE"
    echo "   行数: $line_count"
    
    # 显示前几行
    echo -e "\n📊 文件内容预览:"
    head -3 "$CSV_FILE" | sed 's/^/   /'
    
    if [[ $line_count -gt 3 ]]; then
        echo "   ..."
    fi
else
    echo "❌ 错误: 未找到CSV文件: $CSV_FILE"
    echo "💡 请确保 liked.csv