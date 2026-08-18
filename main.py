import os
import requests
import pandas as pd

# 香港馬會官方廣東話譯名字典
TEAM_MAP = {
    "Arsenal": "阿仙奴", "Coventry City": "高雲地利", "Hull City": "赫爾城",
    "Manchester United": "曼聯", "Everton": "愛華頓", "Crystal Palace": "水晶宮",
    "Ipswich Town": "葉士域治", "Sunderland": "新特蘭", "Nottingham Forest": "諾定咸森林",
    "Leeds United": "列斯聯", "Brentford": "賓福特", "Tottenham Hotspur": "熱刺",
    "Brighton and Hove Albion": "白禮頓", "Aston Villa": "維拉", "Manchester City": "曼城",
    "Bournemouth": "般尼茅夫", "Newcastle United": "紐卡素", "Liverpool": "利物浦",
    "Fulham": "富咸", "Chelsea": "車路士", "Atlético Madrid": "馬德里體育會",
    "Málaga": "馬拉加", "Rayo Vallecano": "華歷簡奴", "Alavés": "阿拉維斯",
    "Real Betis": "皇家貝迪斯", "Real Sociedad": "皇家蘇斯達", "Athletic Bilbao": "畢爾包",
    "Sevilla": "西維爾", "Valencia": "華倫西亞", "Celta Vigo": "施達",
    "Espanyol": "愛斯賓奴", "Real Madrid": "皇家馬德里", "Villarreal": "維拉利爾",
    "Getafe": "基達菲", "Barcelona": "巴塞隆拿", "CA Osasuna": "奧沙辛拿",
    "Udinese": "烏甸尼斯", "Como": "柯謨", "Inter Milan": "國際米蘭",
    "Monza": "蒙沙", "Parma": "帕爾馬", "Cagliari": "卡利亞里", "Genoa": "熱拿亞",
    "Napoli": "拿玻里", "Juventus": "祖雲達斯", "Atalanta BC": "亞特蘭大",
    "AC Milan": "AC米蘭", "Bayern Munich": "拜仁慕尼黑", "VfB Stuttgart": "史圖加特",
    "Bayer Leverkusen": "利華古遜", "RB Leipzig": "萊比錫", "Borussia Dortmund": "多蒙特",
    "Real Racing Club de Santander": "競賽會", "Elche CF": "艾爾切", "Elche": "艾爾切"
}

LEAGUE_MAP = {
    "EPL": "英格蘭超級聯賽",
    "La Liga - Spain": "西班牙甲組聯賽",
    "Serie A - Italy": "義大利甲組聯賽",
    "Bundesliga - Germany": "德國甲組聯賽"
}

def fetch_sports_odds_filtered():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None

    leagues = ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a"]
    matches_list = []
    
    for league_key in leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={api_key}&regions=uk,eu&markets=h2h,spreads"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                events = res.json()
                for event in events:
                    home_eng = event.get("home_team", "")
                    away_eng = event.get("away_team", "")
                    league_eng = event.get("sport_title", "")
                    utc_time = event.get("commence_time", "")
                    
                    if utc_time:
                        hkt_dt = pd.to_datetime(utc_time) + pd.Timedelta(hours=8)
                        date_str = hkt_dt.strftime("%d/%m/%Y")
                        day_char = ["一", "二", "三", "四", "五", "六", "日"][hkt_dt.weekday()]
                        time_str = hkt_dt.strftime("%H:%M")
                        hkt_full = f"{date_str} ({day_char}) {time_str}"
                    else:
                        hkt_full = "-"
                    
                    bookmakers = event.get("bookmakers", [])
                    h_odds, a_odds, h_hdc_line, h_hdc_odds, a_hdc_line, a_hdc_odds = None, None, None, None, None, None
                    
                    if bookmakers:
                        markets = bookmakers[0].get("markets", [])
                        for m in markets:
                            if m.get("key") == "h2h":
                                for outcome in m.get("outcomes", []):
                                    if outcome.get("name") == home_eng:
                                        h_odds = outcome.get("price")
                                    elif outcome.get("name") == away_eng:
                                        a_odds = outcome.get("price")
                            elif m.get("key") == "spreads":
                                for outcome in m.get("outcomes", []):
                                    point = outcome.get("point", 0)
                                    point_str = f"+{point}" if point > 0 else str(point)
                                    if outcome.get("name") == home_eng:
                                        h_hdc_line = point_str
                                        h_hdc_odds = outcome.get("price")
                                    elif outcome.get("name") == away_eng:
                                        a_hdc_line = point_str
                                        a_hdc_odds = outcome.get("price")
                    
                    # 1. 確保有開讓球盤口
                    # 2. 確保水位屬於正常的讓球賠率區間 (<= 2.50)
                    if h_hdc_line is not None and h_hdc_line != "-" and h_hdc_odds and float(h_hdc_odds) <= 2.50:
                        matches_list.append({
                            "香港開賽時間": hkt_full,
                            "聯賽": LEAGUE_MAP.get(league_eng, league_eng),
                            "主隊": TEAM_MAP.get(home_eng, home_eng),
                            "客隊": TEAM_MAP.get(away_eng, away_eng),
                            "主勝(H)": h_odds,
                            "客勝(A)": a_odds,
                            "主讓球盤口": h_hdc_line,
                            "主讓球賠率": h_hdc_odds,
                            "客讓球盤口": a_hdc_line,
                            "客讓球賠率": a_hdc_odds
                        })
        except Exception as e:
            print(f"Error fetching {league_key}: {e}")
            
    return pd.DataFrame(matches_list) if matches_list else None

# 1. 抓取數據與排序
df = fetch_sports_odds_filtered()

if df is not None and not df.empty:
    df = df.sort_values(by="香港開賽時間").reset_index(drop=True)

# 2. 生成全賽事文字列表 (供 Discord 備份)
all_matches_cards = "⚽ **【馬會對應賽事 - 每日讓球盤口總覽】**\n\n"
if df is not None:
    for idx, row in df.iterrows():
        card = f"""📅 **{row['香港開賽時間']} 賽事**
**{row['聯賽']}**
主：{row['主隊']}
客：{row['客隊']}

**讓球盤口 (HDC)：**
主 [{row['主讓球盤口']}] **{row['主讓球賠率']}**
客 [{row['客讓球盤口']}] **{row['客讓球賠率']}**
-----------------------------------"""
        all_matches_cards += card + "\n\n"

# 3. 調用 Gemini API 進行「+EV 期望值與量化勝率分析」
handicap_analysis_card = ""
threads_post = ""
gemini_api_key = os.environ.get("GEMINI_API_KEY")

if gemini_api_key and df is not None:
    sample_data = df.head(6).to_string(index=False)
    
    # 核心勝率與 +EV 分析 Prompt
    card_prompt = f"""
    你是一位職業足球博彩量化分析師。請根據以下最新賽事與讓球數據：

    {sample_data}

    挑選 2-3 場最具下注價值的場次，產出一份「+EV 期望值與勝率分析卡片」。使用貼地香港廣東話，格式如下：

    ⚽ **【馬會對應賽事 - 大數據 +EV 期望值深度分析】**

    📅 **[香港開賽時間] 賽事**
    **[聯賽]**
    主：[主隊] vs 客：[客隊]

    **讓球盤口 (HDC)：**
    主 [[主讓球盤口]] **[主讓球賠率]**  |  客 [[客讓球盤口]] **[客讓球賠率]**

    📊 **大數據量化解析：**
    * **大數據真實淨勝率**：[根據盤口計算出的隱含勝率 %]
    * **+EV 期望值評級**：[說明哪個盤口屬於 +EV 正期望值特價盤，或有折讓價值]
    * **避坑預警**：[說明哪一方屬於熱門低賠率/抽水陷阱]
    🎯 **勝率建議**：[給出明確的推薦與資金下注建議]

    -----------------------------------
    """

    # Threads 引流 Prompt
    threads_prompt = f"""
    你是一位精通馬會足智彩大數據的 Threads 營運專家。請根據數據：
    {sample_data}
    寫一篇 150 字貼地廣東話 Threads 貼文：
    1. 震撼開頭：「今日馬會對照大數據！+EV 特價盤 + 熱門避坑分析已更新！」
    2. 點評 1 場精選讓球盤口（點出其勝率與 +EV 價值）。
    3. 結尾強烈引流：「想獲取每日完整 44+ 場大數據勝率分析？即刻點擊 Bio 連結免費加入 Discord 頻道！」
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    try:
        res1 = requests.post(url, json={"contents": [{"parts": [{"text": card_prompt}]}]}, timeout=15)
        if res1.status_code == 200:
            handicap_analysis_card = res1.json()["candidates"][0]["content"]["parts"][0]["text"]

        res2 = requests.post(url, json={"contents": [{"parts": [{"text": threads_prompt}]}]}, timeout=15)
        if res2.status_code == 200:
            threads_post = res2.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API 出錯: {e}")

# 4. 發送至 Discord Webhook
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    # 1. 發送 Threads 引流草稿
    if threads_post:
        requests.post(webhook_url, data={"content": f"📱 **【今日 Threads 貼文草稿（長按複製）】**\n\n{threads_post}"})
        
    # 2. 發送 +EV 量化分析卡片（核心賣點）
    if handicap_analysis_card:
        requests.post(webhook_url, data={"content": handicap_analysis_card})
    
    # 3. 分段發送全賽事卡片總覽
    if len(all_matches_cards) > 1900:
        chunks = [all_matches_cards[i:i+1900] for i in range(0, len(all_matches_cards), 1900)]
        for chunk in chunks:
            requests.post(webhook_url, data={"content": chunk})
    else:
        requests.post(webhook_url, data={"content": all_matches_cards})

