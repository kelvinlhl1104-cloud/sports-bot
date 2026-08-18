import os
import requests
import pandas as pd

def fetch_real_sports_odds():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None

    leagues = ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a"]
    matches_list = []
    
    for league_key in leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={api_key}&regions=uk,eu&markets=h2h"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                events = res.json()
                for event in events:
                    home_team = event.get("home_team", "")
                    away_team = event.get("away_team", "")
                    utc_time = event.get("commence_time", "")
                    
                    if utc_time:
                        hkt_dt = pd.to_datetime(utc_time) + pd.Timedelta(hours=8)
                        hkt_str = hkt_dt.strftime("%Y-%m-%d %H:%M")
                        day_name = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][hkt_dt.weekday()]
                    else:
                        hkt_str, day_name = "-", "-"
                    
                    bookmakers = event.get("bookmakers", [])
                    h_odds, d_odds, a_odds = None, None, None
                    if bookmakers:
                        outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])
                        for outcome in outcomes:
                            if outcome.get("name") == home_team:
                                h_odds = outcome.get("price")
                            elif outcome.get("name") == away_team:
                                a_odds = outcome.get("price")
                            elif outcome.get("name") == "Draw":
                                d_odds = outcome.get("price")
                    
                    matches_list.append({
                        "聯賽": event.get("sport_title", ""),
                        "星期": day_name,
                        "主隊": home_team,
                        "客隊": away_team,
                        "香港時間 (HKT)": hkt_str,
                        "主勝(H)": h_odds,
                        "和局(D)": d_odds,
                        "客勝(A)": a_odds
                    })
        except Exception as e:
            print(f"Error fetching {league_key}: {e}")
            
    return pd.DataFrame(matches_list) if matches_list else None

# 1. 抓取原始數據
df = fetch_real_sports_odds()

if df is not None and not df.empty:
    # 按時間排序並生成編號
    df = df.sort_values(by="香港時間 (HKT)").reset_index(drop=True)
    df["球賽編號"] = df["星期"] + " " + (df.index + 1).astype(str)

    # 2. 利用 Gemini API 將整張表翻譯為香港馬會中文譯名
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        prompt = f"""
        請將以下足球賽事 JSON 數據中的「聯賽」、「主隊」、「客隊」名稱，100% 翻譯為香港馬會 (HKJC) 官方繁體廣東話譯名。
        例如：Arsenal -> 阿仙奴, Chelsea -> 車路士, Manchester United -> 曼聯, Premier League -> 英格蘭超級聯賽。
        只輸出標準 JSON 陣列格式，不要寫任何多餘的解釋文字。

        數據：
        {df.to_json(orient='records', force_ascii=False)}
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
            if res.status_code == 200:
                raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                cleaned_json = raw_text.replace("```json", "").replace("```", "").strip()
                df = pd.read_json(cleaned_json)
        except Exception as e:
            print(f"翻譯失敗，保留原英文: {e}")

# 3. 調整欄位順序並匯出 Excel
cols = ["球賽編號", "聯賽", "主隊", "客隊", "香港時間 (HKT)", "主勝(H)", "和局(D)", "客勝(A)"]
df = df[[c for c in cols if c in df.columns]]
file_name = "hkjc_daily_odds.xlsx"
df.to_excel(file_name, index=False)

# 4. 發送至 Discord
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    with open(file_name, "rb") as f:
        requests.post(
            webhook_url,
            data={"content": "⚽ **【香港馬會廣東話對照版】熱門賽事與賠率 Excel 已生成！**"},
            files={"file": f}
        )
