import os
import json
import random
import requests
from datetime import datetime, timezone, timedelta

# --- 基础配置 ---
EXAM_DATE = datetime(2026, 2, 20)
START_DATE = datetime(2025, 11, 23)
README_FILE = "README.md"
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"
REPO_URL = "https://github.com/misanthropeli/TOFEL"

# --- 核心修复：绝对安全的替换逻辑 ---
def safe_replace_section(content, start_tag, end_tag, new_content):
    """
    找到 start_tag 和 end_tag，替换中间的内容。
    关键点：确保不引入多余的换行和缩进。
    """
    start_index = content.find(start_tag)
    end_index = content.find(end_tag)
    
    if start_index == -1 or end_index == -1:
        print(f"Warning: Tags {start_tag} or {end_tag} not found. Skipping.")
        return content
    
    # 保留标签，替换中间
    # 这里的 \n 是为了保证源代码可读性，但不会影响 Markdown 渲染
    prefix = content[:start_index + len(start_tag)]
    suffix = content[end_index:]
    return prefix + "\n" + new_content + "\n" + suffix

def get_time_info():
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now + timedelta(hours=8)
    days_left = (EXAM_DATE.date() - beijing_now.date()).days
    total_days = (EXAM_DATE.date() - START_DATE.date()).days
    days_passed = (beijing_now.date() - START_DATE.date()).days
    if total_days <= 0: total_days = 1
    progress = int((days_passed / total_days) * 100)
    return beijing_now, days_left, max(0, min(100, progress))

def make_progress_bar(percent, length=20):
    filled = int(length * percent // 100)
    bar = '■' * filled + '□' * (length - filled)
    return f"[{bar}] {percent}%"

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE): return {}
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def get_current_task_info(hour, schedule):
    routine = schedule.get("daily_routine", {})
    quotes = schedule.get("quotes", ["Go study!"])
    target_key = "08"
    min_diff = 24
    for key in routine.keys():
        try:
            task_hour = int(key)
            diff = hour - task_hour
            if 0 <= diff < min_diff:
                min_diff = diff
                target_key = key
        except: continue
    task_data = routine.get(target_key, {})
    return task_data.get("task", "自主复习"), task_data.get("details", "无具体要求"), random.choice(quotes)

def update_readme(today_date, days_left, progress):
    if not os.path.exists(README_FILE): return

    with open(README_FILE, "r", encoding="utf-8") as f: content = f.read()

    # 1. 更新倒计时 (无缩进字符串)
    html_day = f'<h1 style="font-size: 80px; color: #333; margin: 10px 0;">{days_left} Days</h1>'
    content = safe_replace_section(content, "", "", html_day)

    # 2. 更新进度条 (无缩进字符串)
    p_str = make_progress_bar(progress)
    html_prog = f'<h2 style="font-family: monospace; color: #0052CC;">{p_str}</h2>'
    content = safe_replace_section(content, "", "", html_prog)

    # 3. 更新打卡区
    today_str = today_date.strftime("%Y-%m-%d")
    if f"📅 {today_str}" not in content:
        # 注意：这里列表必须没有前置空格，否则会乱
        new_list = f"""### 📅 {today_str} (Today)
- [ ] **Vocab**: Memorize 100 new words + Review 150
- [ ] **Listening**: Complete 3 SSS Dictations
- [ ] **Reading**: Analyze 5 long sentences from TPO
- [ ] **Output**: Record Speaking Task 1 (3 takes)"""
        content = safe_replace_section(content, "", "", new_list)

    with open(README_FILE, "w", encoding="utf-8") as f: f.write(content)
    print("README Updated Successfully")

def send_feishu(days_left, progress, title, details, quote):
    if not FEISHU_WEBHOOK: return
    color = "blue"
    if days_left < 30: color = "red"
    
    msg = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"倒计时: {days_left} 天 | 进度: {progress}%"},
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**赵大海说：**\n{quote}\n\n---\n**当前任务 ({datetime.now().hour}:00):**\n**{title}**\n{details}"
                    }
                },
                {"tag": "hr"},
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
        requests.post(FEISHU_WEBHOOK, json=msg)
    except Exception as e: print(e)

if __name__ == "__main__":
    now, days, prog = get_time_info()
    schedule = load_schedule()
    update_readme(now, days, prog)
    title, details, quote = get_current_task_info(now.hour, schedule)
    send_feishu(days, prog, title, details, quote)
