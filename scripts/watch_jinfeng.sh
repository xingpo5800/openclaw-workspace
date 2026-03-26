#!/bin/bash
# 金风科技5分钟中枢监控（双向异动版）
# 功能：
#   1. 跌破 27.94 → 止损报警
#   2. 突破 28.75 → 方向选择报警
#   3. 急速拉升 >0.8% in 1min → 异动报警
#   4. 急速下跌 >0.8% in 1min → 异动报警
# 数据源：东方财富

THRESHOLD_DOWN=27.94
THRESHOLD_UP=28.75
SURGE_PCT=0.8      # 1分钟异动幅度%
CHECK_INTERVAL=20   # 秒
STOCK_CODE="0.002202"
STOCK_NAME="金风科技"

PREV_PRICE=""
STATUS="neutral"  # neutral | breached | breakout

alert() {
    local msg="$1"
    say -v "Ting-Ting" "$msg"
    say -v "Ting-Ting" "$msg"
    say -v "Ting-Ting" "$msg"
}

fetch_price() {
    DATA=$(curl -s --max-time 8 \
        "https://push2.eastmoney.com/api/qt/stock/get?secid=$STOCK_CODE&fields=f43,f44,f45" \
        -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" \
        --noproxy '*')
    
    if [ -n "$DATA" ]; then
        PRICE=$(echo "$DATA" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d['data']['f43']/100)
" 2>/dev/null)
        echo "$PRICE"
    fi
}

echo "🚀 金风科技盯盘启动 $(date '+%H:%M:%S')"
echo "   止损位: $THRESHOLD_DOWN | 突破位: $THRESHOLD_UP | 异动阈值: ${SURGE_PCT}%/min"

while true; do
    NOW=$(date "+%H:%M:%S")
    PRICE=$(fetch_price)
    
    if [ -n "$PRICE" ] && [ "$PRICE" != "None" ]; then
        echo "[$NOW] $STOCK_NAME 现价: $PRICE"
        
        # 1. 跌破止损位
        is_down=$(python3 -c "print(1 if float('$PRICE') < $THRESHOLD_DOWN else 0)")
        if [ "$is_down" == "1" ] && [ "$STATUS" == "neutral" ]; then
            echo "🚨 跌破止损位！"
            alert "$STOCK_NAME 跌破止损位 27.94 请注意"
            STATUS="breached"
        fi
        
        # 2. 突破方向选择
        is_up=$(python3 -c "print(1 if float('$PRICE') > $THRESHOLD_UP else 0)")
        if [ "$is_up" == "1" ] && [ "$STATUS" == "neutral" ]; then
            echo "🚀 突破方向！"
            alert "$STOCK_NAME 突破方向选择 28.75 请注意"
            STATUS="breakout"
        fi
        
        # 3. 异动检测（与上一次比较）
        if [ -n "$PREV_PRICE" ] && [ "$PREV_PRICE" != "$PRICE" ]; then
            # 计算变化率
            CHANGE=$(python3 -c "
change = (float('$PRICE') - float('$PREV_PRICE')) / float('$PREV_PRICE') * 100
print(round(change, 2))
" 2>/dev/null)
            
            if [ -n "$CHANGE" ]; then
                IS_SURGE=$(python3 -c "print(1 if abs(float('$CHANGE')) >= $SURGE_PCT else 0)" 2>/dev/null)
                if [ "$IS_SURGE" == "1" ]; then
                    if python3 -c "print(1 if float('$CHANGE') > 0 else 0)" | grep -q 1; then
                        echo "⚡ 急速拉升！涨幅: ${CHANGE}%"
                        alert "$STOCK_NAME 急速拉升 ${CHANGE}%"
                    else
                        echo "⚡ 急速下跌！跌幅: ${CHANGE}%"
                        alert "$STOCK_NAME 急速下跌 ${CHANGE}%"
                    fi
                fi
            fi
        fi
        
        PREV_PRICE="$PRICE"
    else
        echo "[$NOW] 数据获取失败，重试..."
    fi
    
    sleep $CHECK_INTERVAL
done
