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
    "South Melbourne": "南區奇兵", "Sydney FC": "FC悉尼", "Fenerbahce": "費倫巴治", "Lyon": "里昂"
}

LEAGUE_MAP = {
    "EPL": "英格蘭超級聯賽",
    "La Liga - Spain": "西班牙甲組聯賽",
    "Serie A - Italy": "義大利甲組聯賽",
    "Bundesliga - Germany": "德國甲組聯賽",
    "Australia FFA Cup": "澳洲足總盃",
    "UEFA Champions League": "歐洲聯賽冠軍盃"
}

def fetch_sports_odds_with_handicap():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None

    leagues = ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a"]
    matches_list = []
    
    for league_key in leagues:
        # 同時抓取獨贏 (h2h) 與 讓球 (spreads) 盤口
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
                        hkt_str = f"{date_str} ({day_char})"
                    else:
                        hkt_str = "-"
                    
                    bookmakers = event.get("bookmakers", [])
                    h_odds, a_odds, h_hdc_line, h_hdc_odds, a_hdc_line, a_hdc_odds = "-", "-", "-", "-", "-", "-"
                    
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
                    
                    matches_list.append({
                        "聯賽": LEAGUE_MAP.get(league_eng, league_eng),
                        "香港時間": hkt_str,
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

# 1. 抓取數據與生成馬會編號 FB3101 - FB3144
df = fetch_sports_odds_with_handicap()

if df is not None and not df.empty:
    df = df.sort_values(by="香港時間").reset_index(drop=True)
    # 自動編排馬會 FBxxxx 編號格式
    df["球賽編號"] = ["FB" + str(3101 + i) for i in range(len(df))]
    
    cols = ["球賽編號", "聯賽", "主隊", "客隊", "香港時間", "主勝(H)", "客勝(A)", "主讓球盤口", "主讓球賠率", "客讓球盤口", "客讓球賠率"]
    df = df[cols]

file_name = "hkjc_daily_odds.xlsx"
df.to_excel(file_name, index=False)

# 2. 調用 Gemini API 生成帶有「讓球大數據分析」的熱門精選卡片
handicap_analysis_card = ""
threads_post = ""
gemini_api_key = os.environ.get("GEMINI_API_KEY")

if gemini_api_key and df is not None:
    sample_data = df.head(5).to_string(index=False)
    
    # 讓球分析 Prompt
    card_prompt = f"""
    你是一位專業的足球讓球 (Asian Handicap) 大數據分析師。
    以下是最新賽事數據與讓球盤口賠率：

    {sample_data}

    請寫出 2 場熱門賽事的讓球分析卡片，使用廣東話，嚴格按照以下卡片排版輸出：

    📅 **[日期 (星期幾)] 賽事**
    **[球賽編號]，[聯賽]**
    主：[主隊廣東話]
    客：[客隊廣東話]

    **讓球盤口 (HDC)：**
    主 [[主讓球盤口]] **[主讓球賠率]**
    客 [[客讓球盤口]] **[客讓球賠率]**

    💡 **大數據讓球深度分析：**
    * [分析讓球盤口合理性、受讓盤價值或讓球過深風險]
    🎯 **精選建議：** [推薦主/客讓球盤口]

    -----------------------------------
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": card_prompt}]}]}, timeout=15)
        if res.status_code == 200:
            handicap_analysis_card = res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API 出錯: {e}")

# 3. 發送至 Discord
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    if handicap_analysis_card:
        requests.post(webhook_url, data={"content": f"⚽ **【馬會對應賽事 - 讓球大數據分析日報】**\n\n{handicap_analysis_card}"})
    
    with open(file_name, "rb") as f:
        requests.post(webhook_url, data={"content": "⚽ **【每日完整 FBxxxx 馬會編號與讓球賠率 Excel】**"}, files={"file": f})
