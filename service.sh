#!/usr/bin/env bash
# AutoReelStudio Service Controller
# Manages systemd user background service and autostart on system boot

SERVICE_NAME="autoreelstudio.service"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    start)
        echo "🚀 Starting AutoReelStudio systemd background service..."
        systemctl --user start "$SERVICE_NAME"
        systemctl --user status "$SERVICE_NAME" --no-pager
        ;;
    stop)
        echo "🛑 Stopping AutoReelStudio background service..."
        systemctl --user stop "$SERVICE_NAME"
        ;;
    restart)
        echo "🔄 Restarting AutoReelStudio background service..."
        systemctl --user daemon-reload
        systemctl --user restart "$SERVICE_NAME"
        systemctl --user status "$SERVICE_NAME" --no-pager
        ;;
    status)
        systemctl --user status "$SERVICE_NAME" --no-pager
        ;;
    logs)
        echo "📜 Showing live logs for AutoReelStudio (Ctrl+C to exit)..."
        journalctl --user -u "$SERVICE_NAME" -f
        ;;
    enable)
        echo "⚡ Enabling AutoReelStudio to auto-start on system boot..."
        loginctl enable-linger "$USER" 2>/dev/null || true
        systemctl --user daemon-reload
        systemctl --user enable "$SERVICE_NAME"
        echo "✅ Successfully enabled! AutoReelStudio will now launch on system boot."
        ;;
    disable)
        echo "⛔ Disabling AutoReelStudio auto-start on system boot..."
        systemctl --user disable "$SERVICE_NAME"
        echo "✅ Disabled autostart."
        ;;
    *)
        echo "AutoReelStudio Service Controller"
        echo "Usage: $0 {start|stop|restart|status|logs|enable|disable}"
        exit 1
        ;;
esac

