import os
import json
import requests
from datetime import datetime, timedelta, timezone

# --- 配置区域 ---
EXAM_DATE = datetime(2026, 2, 20)
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"

# --- 核心功能 ---

def get_beijing_time():
    # 获取精准的北京时间
    utc_now = datetime.now(timezone.utc)
    return utc_now.astimezone(timezone(timedelta(hours=8)))

def load_schedule():
    # 读取同目录下的 json 计划表
    if not os.path.exists(SCHEDULE_FILE):
        print(f"⚠️ Warning: {SCHEDULE_FILE} not found.")
        return {}
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading JSON: {e}")
        return {}

def send_feishu():
    if not FEISHU_WEBHOOK:
        print("❌ Error: FEISHU_WEBHOOK not set in Secrets.")
        return

    # 1. 准备数据
    bj_now = get_beijing_time()
    days_left = (EXAM_DATE.date() - bj_now.date()).days
    schedule = load_schedule()
    
    # 2. 获取当前任务文案
    hour_str = f"{bj_now.hour:02d}"
    routine = schedule.get("daily_routine", {})
    
    # 简单的任务查找逻辑
    task_info = routine.get(hour_str)
    if not task_info:
        # 如果当前整点没任务，找最近的一个
        for h in ["22", "17", "14", "11", "08"]:
            if bj_now.hour >= int(h):
                task_info = routine.get(h)
                break
    
    title = task_info.get("task", "自由复习/休息") if task_info else "自由复习"
    details = task_info.get("details", "保持专注，积少成多。") if task_info else "查看你的学习清单。"

    # 3. 颜色与标题逻辑
    if days_left < 15:
        color = "carmine"
        header_title = f"💀 仅剩 {days_left} 天 | 红色警报"
    elif days_left < 60:
        color = "orange"
        header_title = f"⚠️ 还有 {days_left} 天 | 保持紧迫"
    else:
        color = "blue"
        header_title = f"备考倒计时: {days_left} 天"

    # 4. 发送请求
    time_str = bj_now.strftime("%Y-%m-%d %H:%M")
    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": header_title},
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md", 
                        "content": f"🕒 **北京时间:** {time_str}\n\n**当前任务：{title}**\n{details}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": "Goal: Chemical Engineering PhD 2027"}]
                }
            ]
        }
    }
    
    try:
        response = requests.post(FEISHU_WEBHOOK, json=data)
        print(f"✅ Feishu sent. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send Feishu: {e}")

if __name__ == "__main__":
    print("🚀 Supervisor Bot Starting...")
    send_feishu()
    print("🏁 Done.")
