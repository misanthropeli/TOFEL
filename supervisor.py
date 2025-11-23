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
REPO_URL = "https://github.com/misanthropeli/TOFEL" # 你的仓库链接

# --- 安全替换函数 (杜绝乱码) ---
def safe_replace(content, start_marker, end_marker, new_content):
    """
    只替换 start_marker 和 end_marker 中间的内容。
    如果找不到标记，就不做任何修改。
    """
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print(f"Warning: Markers {start_marker} or {end_marker} not found.")
        return content
    
    # 保留标记本身，只替换中间
    prefix = content[:start_idx + len(start_marker)]
    suffix = content[end_idx:]
    
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
    filled_length = int(length * percent // 100)
    bar = '■' * filled_length + '□' * (length - filled_length)
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
    if not os.path.exists(README_FILE): 
        print("README not found!")
        return

    with open(README_FILE, "r", encoding="utf-8") as f: content = f.read()

    # 1. 更新倒计时
    new_day_html = f'      <h1 style="font-size: 80px; color: #333; margin: 10px 0;">{days_left} Days</h1>'
    content = safe_replace(content, "", "", new_day_html)

    # 2. 更新进度条
    progress_str = make_progress_bar(progress)
    new_prog_html = f'      <h2 style="font-family: monospace; color: #0052CC;">{progress_str}</h2>'
    content = safe_replace(content, "", "", new_prog_html)

    # 3. 更新打卡区
    today_str = today_date.strftime("%Y-%m-%d")
    # 只有当日期标题不是今天时，才生成新的
    if f"📅 {today_str}" not in content:
        new_checklist = f"""### 📅 {today_str} (Today)
- [ ] **Vocab**: Memorize 100 new words + Review 150
- [ ] **Listening**: Complete 3 SSS Dictations (Error < 5 words)
- [ ] **Reading**: Analyze 5 long sentences from TPO
- [ ] **Output**: Record Speaking Task 1 (3 takes)"""
        content = safe_replace(content, "", "", new_checklist)

    with open(README_FILE, "w", encoding="utf-8") as f: f.write(content)
    print(f"README updated successfully.")

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
    
    # 1. 更新文件
    update_readme(now, days, prog)
    
    # 2. 发送消息
    title, details, quote = get_current_task_info(now.hour, schedule)
    send_feishu(days, prog, title, details, quote)
