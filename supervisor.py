import os
import json
import requests
from datetime import datetime, timedelta, timezone

# --- 配置区域 ---
EXAM_DATE = datetime(2026, 2, 20)
# 请将下面的链接换成你自己的仓库链接，方便你点击跳转
REPO_URL = "https://github.com/" 
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"

def get_time_info():
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now + timedelta(hours=8)
    days_left = (EXAM_DATE.date() - beijing_now.date()).days
    return beijing_now, days_left

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return {}
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_current_task(hour, days_left, schedule):
    sprint_days = schedule.get("sprint_mode_trigger_days", 15)
    if days_left <= sprint_days:
        return "🚨 考前地狱冲刺", schedule.get("sprint_message", "模考！模考！模考！")

    routine = schedule.get("daily_routine", {})
    hour_str = f"{hour:02d}"
    
    task_info = routine.get(hour_str)
    if not task_info:
        sorted_keys = sorted(routine.keys())
        for k in reversed(sorted_keys):
            if int(k) <= hour:
                task_info = routine[k]
                break
    
    if task_info:
        return task_info.get("task"), task_info.get("details")
    else:
        return "休息/自由复习", "保持清醒，准备下一个 Time Block。"

def send_feishu(title, content, days_left):
    if not FEISHU_WEBHOOK:
        print("No Webhook found. Skipping Feishu notification.")
        return

    if days_left < 15:
        color = "carmine" 
        header_title = f"💀 距离审判日仅剩 {days_left} 天"
    elif days_left < 60:
        color = "orange"
        header_title = f"⚠️ 距离考试还有 {days_left} 天"
    else:
        color = "blue"
        header_title = f"📅 托福备考倒计时: {days_left} 天"

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
                        "content": f"**当前任务：{title}**\n\n{content}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": "Chemical Engineering PhD 2027 | No Excuses."}]
                },
                {
                    "tag": "action",
                    "actions": [{
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "✅ 去 GitHub 打卡"},
                        "url": REPO_URL,
                        "type": "primary"
                    }]
                }
            ]
        }
    }
    
    try:
        requests.post(FEISHU_WEBHOOK, json=data)
        print(f"Sent: {title}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    now, days_left = get_time_info()
    schedule = load_schedule()
    task_title, task_details = get_current_task(now.hour, days_left, schedule)
    send_feishu(task_title, task_details, days_left)
