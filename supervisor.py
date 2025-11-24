import os
import re
import json
import requests
from datetime import datetime, timedelta, timezone

# --- 配置区域 ---
EXAM_DATE = datetime(2026, 2, 20)
REPO_URL = "https://github.com/misanthropeli/TOFEL" 
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"
README_FILE = "README.md"

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now.astimezone(timezone(timedelta(hours=8)))
    return beijing_now

def update_readme(days_left):
    if not os.path.exists(README_FILE):
        print(f"Error: {README_FILE} not found.")
        return False

    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 安全检查：如果读取为空，直接停止
    if len(content) < 10:
        print("❌ Error: README seems empty. Aborting.")
        return False

    # 核心修复：更严谨的正则，防止匹配到整个文件
    # 只匹配 数字pattern = r"().*?()"
    replacement = f"\\g<1>{days_left}\\g<2>"
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content)
        
        # --- 安全锁 ---
        # 如果新内容长度太短，说明出事了，拒绝写入
        if len(new_content) < 100:
            print(f"❌ SAFETY LOCK ENGAGED: New content too short ({len(new_content)} chars). Prevented overwrite.")
            print("Content dump:", new_content)
            return False
        # --------------

        if new_content != content:
            with open(README_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ README updated to {days_left} days.")
            return True
        else:
            print("ℹ️ Days unchanged.")
            return False
    else:
        print("❌ Error: Countdown markers not found in README.")
        return False

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
        found_key = None
        for k in reversed(sorted_keys):
            if int(k) <= hour:
                found_key = k
                break
        if found_key:
            task_info = routine[found_key]

    if task_info:
        return task_info.get("task"), task_info.get("details")
    else:
        return "💤 休息/自由复习", "保持清醒，准备下一个 Time Block。"

def send_feishu(beijing_now, title, content, days_left):
    if not FEISHU_WEBHOOK:
        return

    if days_left < 15:
        color = "carmine" 
        header_title = f"💀 仅剩 {days_left} 天 | 冲刺警报"
    else:
        color = "blue"
        header_title = f"备考倒计时: {days_left} 天"

    time_str = beijing_now.strftime("%Y-%m-%d %H:%M")

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
                        "content": f"🕒 **当前时间:** {time_str}\n\n---\n**当前任务：{title}**\n{content}"
                    }
                },
                {
                    "tag": "hr"
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
        print("Feishu notification sent.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    bj_now = get_beijing_time()
    days_left = (EXAM_DATE.date() - bj_now.date()).days
    
    # 执行更新
    update_readme(days_left)
    
    # 发送飞书
    schedule = load_schedule()
    task_title, task_details = get_current_task(bj_now.hour, days_left, schedule)
    send_feishu(bj_now, task_title, task_details, days_left)
