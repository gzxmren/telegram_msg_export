#!/bin/bash

# =================================================================
# TG-Link-Dispatcher 管理脚本 (v1.0)
# =================================================================

SERVICE_NAME="tg-export"
PROJECT_DIR="/home/xmren/gemini/telegram_msg_export"

# 确保在项目根目录下运行
cd "$PROJECT_DIR" || { echo "❌ 无法进入项目目录: $PROJECT_DIR"; exit 1; }

function check_status() {
    # 检查服务是否通过 systemctl 加载
    if systemctl list-unit-files "$SERVICE_NAME.service" | grep -q "$SERVICE_NAME.service"; then
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo "🟢 Systemd 服务正在运行 (PID: $(systemctl show --property MainPID --value "$SERVICE_NAME"))"
            return 0
        else
            echo "⚪ Systemd 服务已加载但未运行"
            return 1
        fi
    else
        echo "⚠️  Systemd 服务 [$SERVICE_NAME] 尚未安装"
        return 2
    fi
}

case "$1" in
    start)
        echo "[*] 正在尝试启动后台服务..."
        sudo systemctl start "$SERVICE_NAME"
        sleep 1
        check_status
        ;;
    stop)
        echo "[*] 正在停止后台服务..."
        sudo systemctl stop "$SERVICE_NAME"
        echo "✅ 已停止"
        ;;
    restart)
        echo "[*] 正在重启后台服务..."
        sudo systemctl restart "$SERVICE_NAME"
        sleep 1
        check_status
        ;;
    status)
        check_status
        ;;
    run)
        # 前台调试模式
        status_code=$(check_status > /dev/null; echo $?)
        if [ "$status_code" -eq 0 ]; then
            echo "⚠️  后台服务正在运行。"
            read -p "👉 是否先停止后台服务，再进入前台模式? (y/N) " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                sudo systemctl stop "$SERVICE_NAME"
                echo "✅ 后台服务已停止"
            else
                echo "❌ 操作取消，前台模式无法启动 (避免冲突)"
                exit 0
            fi
        fi
        
        echo "🚀 启动前台调试模式 (按 Ctrl+C 退出)..."
        echo "--------------------------------------------------"
        python3 main_dispatcher.py --web
        ;;
    logs)
        echo "[*] 正在查看系统日志 (实时滚动，按 Ctrl+C 退出)..."
        journalctl -u "$SERVICE_NAME" -f -n 50
        ;;
    list)
        # 我们的 list_chats.py 已经支持混合模式，会自动判断是否走 API
        python3 list_chats.py
        ;;
    install)
        # 自动化安装 Service 文件的引导
        echo "[*] 正在生成 Systemd 服务文件..."
        cat <<EOF | sudo tee /etc/systemd/system/$SERVICE_NAME.service
[Unit]
Description=Telegram Message Dispatcher Service
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=xmren
Group=xmren
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 main_dispatcher.py --daemon --web
Restart=always
RestartSec=60s
StartLimitInterval=600
StartLimitBurst=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        echo "✅ 服务文件已安装到 /etc/systemd/system/$SERVICE_NAME.service"
        echo "💡 现在你可以运行 './manage.sh start' 来启动它了。"
        ;;
    *)
        echo "TG-Link-Dispatcher 控制中心"
        echo "--------------------------------------------------"
        echo "用法: $0 {start|stop|restart|status|run|logs|list|install}"
        echo ""
        echo "  start   : 启动 Systemd 后台服务"
        echo "  stop    : 停止 Systemd 后台服务"
        echo "  restart : 重启 Systemd 后台服务"
        echo "  status  : 检查当前服务状态"
        echo "  run     : 停止后台模式，以交互式前台模式运行 (用于调试)"
        echo "  logs    : 查看后台日志 (journalctl)"
        echo "  list    : 运行 list_chats.py (无锁模式)"
        echo "  install : (首次执行) 安装/更新 Systemd 配置文件"
        echo "--------------------------------------------------"
        exit 1
        ;;
esac
