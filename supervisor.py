import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta

# --- CONFIGURATION ---
EXAM_DATE = datetime(2026, 2, 20)
START_DATE = datetime(2025, 11, 23)
README_FILE = "README.md"
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"

def get_time_info():
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now + timedelta(hours=8)
    
    days_left = (EXAM_DATE.date() - beijing_now.date()).days
    total_days = (EXAM_DATE.date() - START_DATE.date()).days
    days_passed = (beijing_now.date() - START_DATE.date()).days
    
    if total_days <= 0: total_days = 1
    progress = int((days_passed / total_days) * 100)
    
    return beijing_now, days_left, max(0, min(100, progress))

def update_readme(today_date, days_left, progress):
    if not os.path.exists(README_FILE): return

    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 更新天数 (Day Counter)
    # 匹配 和 之间的任何内容
    pattern_days = r"(\n)(.*?)(\n\s*)"
    # 我们保留原来的样式 style="...", 只替换数字
    # 注意：这里的替换字符串包含 HTML 样式，确保视觉效果不变
    new_day_html = f'      <h1 style="font-size: 80px; color: #333;">{days_left} Days</h1>'
    
    if re.search(pattern_days, content, re.DOTALL):
        content = re.sub(pattern_days, f"\\g<1>{new_day_html}\\g<3>", content, flags=re.DOTALL)

    # 2. 更新总进度条 (Total Progress)
    pattern_prog = r"(\n)(.*?)(\n)"
    new_img_tag = f'<img src="https://progress-bar.dev/{progress}/?scale=100&title=Total_Preparation&width=500&color=0052CC&suffix=%25" alt="Total Progress">'
    
    if re.search(pattern_prog, content, re.DOTALL):
        content = re.sub(pattern_prog, f"\\g<1>{new_img_tag}\\g<3>", content, flags=re.DOTALL)

    # 3. 每日打卡区重置 (Daily Checklist)
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

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"README Updated: {days_left} days left, {progress}% progress.")

def send_feishu(days_left):
    if not FEISHU_WEBHOOK: return
    
    msg = {
        "msg_type": "text",
        "content": {
            "text": f"🌊 早安！实验开始了。距离 TOEFL 考试还有 {days_left} 天。\nCheck your GitHub Dashboard now."
        }
    }
    try:
        requests.post(FEISHU_WEBHOOK, json=msg)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    now, days, prog = get_time_info()
    update_readme(now, days, prog)
    
    if now.hour == 8:
        send_feishu(days)
