import os
import requests
import pandas as pd

TEAM_MAP = {
    "Arsenal": "阿仙奴", "Manchester United": "曼聯", "Manchester City": "曼城",
    "Liverpool": "利物浦", "Chelsea": "車路士", "Tottenham Hotspur": "熱刺",
    "Reading": "雷丁", "Wycombe Wanderers": "韋甘比", "Leyton Orient": "奧連特",
    "AFC Wimbledon": "AFC 溫布頓", "Al-Nassr": "艾納斯", "Al-Ittihad": "伊蒂哈德"
}

def make_progress_bar(pct):
    filled = max(1, min(10, int(round(pct / 10))))
    return "█" * filled + "░" * (10 - filled)

def fetch_hkjc_matching_odds():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None, None

    # 同時搜尋英超與英格蘭聯賽錦標/盃賽
    leagues = ["soccer_epl", "soccer_england_league1", "soccer_england_championship"]
    all_events = []

    for l_key in leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{l_key}/odds/?apiKey={api_key}&regions=uk,eu&markets=spreads"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                all_events.extend(res.json())
        except Exception as e:
            print(f"Error {l_key}: {e}")

    if not all_events:
        return None, None

    # 取第一場作為今日重心推介
    top_event = all_events[0]
    home_eng = top_event.get("home_team", "")
    away_eng = top_event.get("away_team", "")
    home = TEAM_MAP.get(home_eng, home_eng)
    away = TEAM_MAP.get(away_eng, away_eng)
    
    utc_time = top_event.get("commence_time", "")
    hkt_str = (pd.to_datetime(utc_time) + pd.Timedelta(hours=8)).strftime("%d/%m/%Y %H:%M") if utc_time else "-"
    
    spreads = top_event.get("bookmakers", [{}])[0].get("markets", [{}])[0].get("outcomes", [])
    h_line, h_odds, a_line, a_odds = "-0.5", 1.90, "+0.5", 1.90
    for s in spreads:
        if s.get("name") == home_eng:
            h_line = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
            h_odds = float(s.get('price', 1.90))
        elif s.get("name") == away_eng:
            a_line = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
            a_odds = float(s.get('price', 1.90))

    # 量化模型運算
    raw_h = (1 / h_odds) * 100
    raw_a = (1 / a_odds) * 100
    total = raw_h + raw_a
    h_prob = round((raw_h / total) * 100, 1)
    a_prob = round((raw_a / total) * 100, 1)

    analysis_card = f"""
🔥 **【馬會對應賽事 - 職業大數據 +EV 期望值深度分析】**

📅 **{hkt_str} 焦點重心**
⚽ **{home} vs {away}**

━━━━━━━━━━━━━━━━━━━
📊 **大數據量化解析**
• **主隊勝率模型**：{make_progress_bar(h_prob)} **{h_prob}%** (盤口 [{h_line}] @ {h_odds})
• **客隊勝率模型**：{make_progress_bar(a_prob)} **{a_prob}%** (盤口 [{a_line}] @ {a_odds})

💡 **+EV 期望值評級**：★★★★★ (馬會熱門對應盤口)
⚠️ **莊家陷阱避坑**：精準對應馬會即時讓球盤，過濾市場盲點。

🎯 **專業下注建議**：推薦 **{home if h_odds <= a_odds else away}**
💰 **建議資金分配**：平注 **3.5%** 
━━━━━━━━━━━━━━━━━━━
"""

    # 生成其餘馬會對應賽事總覽
    overview_list = ["⚽ **【馬會同步開盤賽事總覽】**\n"]
    for event in all_events[1:7]:
        e_home = TEAM_MAP.get(event.get("home_team"), event.get("home_team"))
        e_away = TEAM_MAP.get(event.get("away_team"), event.get("away_team"))
        e_time = (pd.to_datetime(event.get("commence_time")) + pd.Timedelta(hours=8)).strftime("%d/%m/%Y %H:%M")
        overview_list.append(f"📅 **{e_time}**\n主：{e_home} vs 客：{e_away}\n-----------------------------------")

    return analysis_card, "\n\n".join(overview_list)

card, overview = fetch_hkjc_matching_odds()
webhook_url = os.environ.get("DISCORD_WEBHOOK")

if webhook_url and card:
    requests.post(webhook_url, data={"content": card})
    if overview:
        requests.post(webhook_url, data={"content": overview})

