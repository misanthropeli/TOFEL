import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta

# --- 基础配置 ---
EXAM_DATE = datetime(2026, 2, 20)
START_DATE = datetime(2025, 11, 23)
README_FILE = "README.md"
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"

def get_time_info():
    # 获取北京时间
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now + timedelta(hours=8)
    
    days_left = (EXAM_DATE.date() - beijing_now.date()).days
    total_days = (EXAM_DATE.date() - START_DATE.date()).days
    days_passed = (beijing_now.date() - START_DATE.date()).days
    
    # 进度计算
    if total_days <= 0: total_days = 1
    progress = int((days_passed / total_days) * 100)
    
    return beijing_now, days_left, max(0, min(100, progress))

# --- 核心功能：生成字符进度条 ---
def make_progress_bar(percent, length=20):
    filled_length = int(length * percent // 100)
    bar = '■' * filled_length + '□' * (length - filled_length)
    return f"[{bar}] {percent}%"

def update_readme(today_date, days_left, progress):
    if not os.path.exists(README_FILE): 
        print(f"Error: {README_FILE} not found.")
        return

    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 更新倒计时 (保留你的 H1 样式)
    pattern_days = r"(\n)(.*?)(\n\s*)"
    new_day_html = f'      <h1 style="font-size: 80px; color: #333; margin: 10px 0;">{days_left} Days</h1>'
    
    if re.search(pattern_days, content, re.DOTALL):
        content = re.sub(pattern_days, f"\\g<1>{new_day_html}\\g<3>", content, flags=re.DOTALL)

    # 2. 更新进度条 (生成字符画)
    pattern_prog = r"(\n)(.*?)(\n\s*)"
    progress_str = make_progress_bar(progress)
    new_prog_html = f'      <h2 style="font-family: monospace; color: #0052CC;">{progress_str}</h2>'
    
    if re.search(pattern_prog, content, re.DOTALL):
        content = re.sub(pattern_prog, f"\\g<1>{new_prog_html}\\g<3>", content, flags=re.DOTALL)

    # 3. 每日打卡区 (如果是新的一天，重置 Checklist)
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

def send_feishu(days_left, progress):
    if not FEISHU_WEBHOOK:
        print("Feishu Webhook not set.")
        return
    
    # 这里的文案可以根据剩余天数自动变化
    msg_title = "💪 保持专注 (Stay Focused)"
    if days_left < 30:
        msg_title = "🔥 红色警报 (Red Alert)"
    
    msg = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"PhD Countdown: {days_left} Days"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{msg_title}**\n当前进度: {progress}%\n请前往 GitHub 完成今日打卡。"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "✅ 去打卡 / Check In"
                            },
                            "url": "https://github.com/misanthropeli/TOFEL", 
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(FEISHU_WEBHOOK, json=msg)
        print(f"Feishu sent. Response: {response.text}")
    except Exception as e:
        print(f"Feishu error: {e}")

if __name__ == "__main__":
    now, days, prog = get_time_info()
    
    # 1. 更新文件
    update_readme(now, days, prog)
    
    # 2. 发送消息 (不再限制时间，只要运行就发)
    send_feishu(days, prog)
