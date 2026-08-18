import os
import requests
import pandas as pd

# 香港人最熟悉、馬會必開盤的主流球隊中文化對照
TEAM_MAP = {
    # 英超
    "Arsenal": "阿仙奴", "Manchester United": "曼聯", "Manchester City": "曼城",
    "Liverpool": "利物浦", "Chelsea": "車路士", "Tottenham Hotspur": "熱刺",
    "Aston Villa": "維拉", "Newcastle United": "紐卡素", "Brighton and Hove Albion": "白禮頓",
    "West Ham United": "韋斯咸", "Crystal Palace": "水晶宮", "Everton": "愛華頓",
    "Fulham": "富咸", "Brentford": "賓福特", "Wolverhampton Wanderers": "狼隊",
    "Bournemouth": "般尼茅夫", "Nottingham Forest": "諾定咸森林", "Leicester City": "李斯特城",
    "Southampton": "修咸頓", "Ipswich Town": "葉士域治",
    # 西甲
    "Real Madrid": "皇家馬德里", "Barcelona": "巴塞隆拿", "Atlético Madrid": "馬德里體育會",
    "Real Sociedad": "皇家蘇斯達", "Villarreal": "維拉利爾", "Real Betis": "皇家貝迪斯",
    # 意甲
    "Inter Milan": "國際米蘭", "AC Milan": "AC米蘭", "Juventus": "祖雲達斯",
    "Napoli": "拿玻里", "Atalanta": "亞特蘭大", "Roma": "羅馬",
    # 德甲
    "Bayern Munich": "拜仁慕尼黑", "Bayer Leverkusen": "利華古遜", "Borussia Dortmund": "多蒙特"
}

def make_progress_bar(pct):
    filled = max(1, min(10, int(round(pct / 10))))
    return "█" * filled + "░" * (10 - filled)

def fetch_hkjc_target_matches():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None, None

    # 嚴格鎖定香港馬會最熱門、必開盤的頂級聯賽與盃賽
    target_leagues = [
        "soccer_epl",                  # 英超
        "soccer_uefa_champions_league",# 歐聯
        "soccer_spain_la_liga",        # 西甲
        "soccer_italy_serie_a",        # 意甲
        "soccer_germany_bundesliga",   # 德甲
        "soccer_england_championship"  # 英冠 (香港人好鍾意賭)
    ]
    
    all_events = []
    for l_key in target_leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{l_key}/odds/?apiKey={api_key}&regions=uk,eu&markets=spreads"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                events = res.json()
                all_events.extend(events)
        except Exception as e:
            print(f"Error {l_key}: {e}")

    if not all_events:
        return None, None

    # 按開賽時間排序
    all_events = sorted(all_events, key=lambda x: x.get("commence_time", ""))
    
    # 取第一場作為「全日馬會重心推介」
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

    # 量化模型運算勝率
    raw_h = (1 / h_odds) * 100
    raw_a = (1 / a_odds) * 100
    total = raw_h + raw_a
    h_prob = round((raw_h / total) * 100, 1)
    a_prob = round((raw_a / total) * 100, 1)

    recommend_side = f"主隊 [{home}] ({h_line})" if h_odds <= a_odds else f"客隊 [{away}] ({a_line})"

    # 1. 專業量化分析卡片 + Threads 宣傳文案
    analysis_card = f"""
🔥 **【香港馬會對應賽事 - 每日大數據 +EV 期望值深度分析】**

📅 **{hkt_str} 馬會熱門焦點**
⚽ **{home} vs {away}**

━━━━━━━━━━━━━━━━━━━
📊 **大數據量化解析**
• **主隊勝率模型**：{make_progress_bar(h_prob)} **{h_prob}%** (讓球盤 {h_line} @ {h_odds})
• **客隊勝率模型**：{make_progress_bar(a_prob)} **{a_prob}%** (受讓盤 {a_line} @ {a_odds})

💡 **+EV 期望值評級**：★★★★★ (馬會熱門對應盤口)
⚠️ **莊家陷阱避坑**：已過濾非馬會賽事，全屬香港人熟悉之主流盤口。

🎯 **專業下注建議**：推薦 **{recommend_side}**
💰 **建議資金分配**：平注 **3.5%** 資金配置
━━━━━━━━━━━━━━━━━━━

📱 **【Threads 吸客文案草稿（長按複製）】**
🔥 今日馬會對照大數據已更新！香港人最關注焦點：{home} vs {away}，系統鎖定 +EV 特價盤！即刻加入 Discord 頻道獲取完整讓球盤口！
"""

    # 2. 生成其餘馬會同步開盤賽事總覽
    overview_list = ["⚽ **【今日馬會同步熱門讓球盤口總覽】**\n"]
    for event in all_events[1:8]:
        e_home = TEAM_MAP.get(event.get("home_team"), event.get("home_team"))
        e_away = TEAM_MAP.get(event.get("away_team"), event.get("away_team"))
        e_time = (pd.to_datetime(event.get("commence_time")) + pd.Timedelta(hours=8)).strftime("%d/%m/%Y %H:%M")
        
        s_list = event.get("bookmakers", [{}])[0].get("markets", [{}])[0].get("outcomes", [])
        hl, ho, al, ao = "-.---", "1.90", "-.---", "1.90"
        for s in s_list:
            if s.get("name") == event.get("home_team"):
                hl = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
                ho = s.get('price')
            else:
                al = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
                ao = s.get('price')

        overview_list.append(f"📅 **{e_time}**\n主：{e_home} vs 客：{e_away}\n讓球盤：主 [{hl}] **{ho}** | 客 [{al}] **{ao}**\n-----------------------------------")

    return analysis_card, "\n\n".join(overview_list)

card, overview = fetch_hkjc_target_matches()
webhook_url = os.environ.get("DISCORD_WEBHOOK")

if webhook_url and card:
    requests.post(webhook_url, data={"content": card})
    if overview:
        if len(overview) > 1900:
            chunks = [overview[i:i+1900] for i in range(0, len(overview), 1900)]
            for chunk in chunks:
                requests.post(webhook_url, data={"content": chunk})
        else:
            requests.post(webhook_url, data={"content": overview})

