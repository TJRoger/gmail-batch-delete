#!/bin/bash
# Gmail 邮件批量删除 Web 服务启动脚本

echo "启动 Gmail 邮件批量删除 Web 服务..."
echo ""

# 检查Python版本
python3 --version

# 检查依赖
echo "检查依赖包..."
pip3 install -r requirements.txt

# 启动服务
echo ""
echo "启动Web服务..."
echo "访问地址: http://localhost:5004"
echo ""
python3 app.py




