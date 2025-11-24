import os
import re
import json
import requests
from datetime import datetime, timedelta, timezone

# --- 配置区域 ---
EXAM_DATE = datetime(2026, 2, 20)
REPO_URL = "https://github.com/misanthropeli/TOFEL"  # 记得换成你自己的仓库地址
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"
README_FILE = "README.md"

def get_beijing_time():
    # 强制转换为北京时间 (UTC+8)
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now.astimezone(timezone(timedelta(hours=8)))
    return beijing_now

def update_readme(days_left):
    """
    使用 HTML 注释标记 进行精准替换
    """
    if not os.path.exists(README_FILE):
        print(f"Error: {README_FILE} not found.")
        return False

    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 核心逻辑：寻找 任意数字# 并将其替换为新的天数
    pattern = r"().*?()"
    replacement = f"\\g<1>{days_left}\\g<2>"
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content)
        
        # 只有当内容真的改变时才写入，避免无效提交
        if new_content != content:
            with open(README_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ README updated to {days_left} days.")
            return True
        else:
            print("ℹ️ Days unchanged. No update needed.")
            return False
    else:
        print("❌ Error: Countdown markers not found in README.")
        print("Please ensure your README contains: Number")
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
    
    # 如果当前小时没任务，找最近的一个
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
    elif days_left < 60:
        color = "orange"
        header_title = f"⚠️ 还有 {days_left} 天 | 紧迫感呢？"
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
                        "content": f"**当前时间 (BJ):** {time_str}\n\n---\n**当前任务：{title}**\n{content}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "action",
                    "actions": [{
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "去 GitHub 打卡"},
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
    # 1. 获取时间
    bj_now = get_beijing_time()
    # 2. 计算剩余天数
    days_left = (EXAM_DATE.date() - bj_now.date()).days
    
    print(f"Current Beijing Time: {bj_now}")
    print(f"Days Left: {days_left}")

    # 3. 更新 README (使用新的锚点逻辑)
    update_readme(days_left)
    
    # 4. 发送飞书提醒
    schedule = load_schedule()
    task_title, task_details = get_current_task(bj_now.hour, days_left, schedule)
    send_feishu(bj_now, task_title, task_details, days_left)
