#!/bin/bash

# hq_job server 管理脚本
# 用法: ./start.sh [start|stop|restart|status]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/hq_job.pid"
LOG_FILE="${SCRIPT_DIR}/hq_job.log"

# 环境变量配置
export AUTODL_TOKEN="eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjY3MzAyNCwidXVpZCI6IjUxNWEyNzg5ZDgwMzdlZmEiLCJpc19hZG1pbiI6ZmFsc2UsImJhY2tzdGFnZV9yb2xlIjoiIiwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJzdWJfbmFtZSI6IiIsInRlbmFudCI6ImF1dG9kbCIsInVwayI6IiJ9.Z7ehfhzgIStE3_7RTiinhlkYxGA2i1yoPZbWce9DFiQt4iTuenJWJP4V0iT45VGCWTcS43Lw4iZKwYD7APxfzw"
export API_TOKEN="foresee_hq_job"
export HQJOB_COS_PREFIX="cos://autodl"

start() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "hq_job server 已经在运行中 (PID: $OLD_PID)"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    cd "$SCRIPT_DIR"
    echo "正在启动 hq_job server..."
    nohup python -m hq_job.server > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"

    sleep 2
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "hq_job server 启动成功 (PID: $PID)"
        echo "日志文件: $LOG_FILE"
    else
        echo "hq_job server 启动失败，请查看日志: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "PID 文件不存在，服务可能未运行"
        return 0
    fi

    PID=$(cat "$PID_FILE")
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "进程 $PID 不存在，清理 PID 文件"
        rm -f "$PID_FILE"
        return 0
    fi

    echo "正在停止 hq_job server (PID: $PID)..."
    kill "$PID"

    TIMEOUT=10
    COUNT=0
    while ps -p "$PID" > /dev/null 2>&1; do
        if [ $COUNT -ge $TIMEOUT ]; then
            echo "进程未能正常停止，强制终止..."
            kill -9 "$PID"
            break
        fi
        sleep 1
        COUNT=$((COUNT + 1))
    done

    rm -f "$PID_FILE"
    echo "hq_job server 已停止"
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "hq_job server 正在运行 (PID: $PID)"
        else
            echo "hq_job server 未运行 (PID 文件存在但进程不存在)"
        fi
    else
        echo "hq_job server 未运行"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac