import os
import re
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
REPO_URL = "https://github.com/misanthropeli/TOFEL" # 你的仓库链接

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
    filled_length = int(length * percent // 100)
    bar = '■' * filled_length + '□' * (length - filled_length)
    return f"[{bar}] {percent}%"

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE): return {}
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f: return json.load(f)

# 获取当前时间段的任务
def get_current_task_info(hour, schedule):
    routine = schedule.get("daily_routine", {})
    quotes = schedule.get("quotes", ["Go study!"])
    
    # 找到最近的一个时间点
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

    # 1. 精准更新倒计时 (只替换数字部分，保留样式)
    # 使用 strict regex 确保只匹配到我们要的地方
    pattern_days = r"(\n)(.*?)(\n\s*)"
    new_day_html = f'      <h1 style="font-size: 80px; color: #333; margin: 10px 0;">{days_left} Days</h1>'
    if re.search(pattern_days, content, re.DOTALL):
        content = re.sub(pattern_days, f"\\g<1>{new_day_html}\\g<3>", content, flags=re.DOTALL)

    # 2. 精准更新进度条
    pattern_prog = r"(\n)(.*?)(\n\s*)"
    progress_str = make_progress_bar(progress)
    new_prog_html = f'      <h2 style="font-family: monospace; color: #0052CC;">{progress_str}</h2>'
    if re.search(pattern_prog, content, re.DOTALL):
        content = re.sub(pattern_prog, f"\\g<1>{new_prog_html}\\g<3>", content, flags=re.DOTALL)

    # 3. 每日打卡区
    today_str = today_date.strftime("%Y-%m-%d")
    if f"📅 {today_str}" not in content:
        new_checklist = f"""### 📅 {today_str} (Today)
- [ ] **Vocab**: Memorize 100 new words + Review 150
- [ ] **Listening**: Complete 3 SSS Dictations (Error < 5 words)
- [ ] **Reading**: Analyze 5 long sentences from TPO
- [ ] **Output**: Record Speaking Task 1 (3 takes)"""
        pattern_check = r"(\n)(.*?)(\n)"
        if re.search(pattern_check, content, re.DOTALL):
            content = re.sub(pattern_check, f"\\g<1>{new_checklist}\\g<3>", content, flags=re.DOTALL)

    with open(README_FILE, "w", encoding="utf-8") as f: f.write(content)

def send_feishu(days_left, progress, title, details, quote):
    if not FEISHU_WEBHOOK: return
    
    color = "blue"
    if days_left < 30: color = "red"
    
    # 构造更详细的消息卡片
    msg = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📅 倒计时: {days_left} 天 | 进度: {progress}%"},
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**💡 监督员说：**\n{quote}\n\n---\n**🚩 当前任务 ({datetime.now().hour}:00):**\n**{title}**\n{details}"
                    }
                },
                {"tag": "hr"},
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
        requests.post(FEISHU_WEBHOOK, json=msg)
    except Exception as e: print(e)

if __name__ == "__main__":
    now, days, prog = get_time_info()
    schedule = load_schedule()
    
    # 1. 更新文件
    update_readme(now, days, prog)
    
    # 2. 获取任务详情
    title, details, quote = get_current_task_info(now.hour, schedule)
    
    # 3. 发送详细消息
    send_feishu(days, prog, title, details, quote)
