import os
import requests
import pandas as pd

def fetch_hkjc_odds():
    """模擬真實瀏覽器抓取馬會即時賠率"""
    url = "https://bet.hkjc.com/football/getJSON.aspx?jsontype=odds_had.aspx"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://bet.hkjc.com/ch/football/home",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 先訪問主頁獲取 Cookie 繞過阻擋
        session.get("https://bet.hkjc.com/ch/football/home", timeout=10)
        res = session.get(url, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            matches = data.get("matches", [])
            matches_list = []
            
            for m in matches:
                match_id = m.get("bno", m.get("matchNum", ""))
                league = m.get("league", {}).get("leagueNameCH", "")
                home_team = m.get("homeTeam", {}).get("teamNameCH", "")
                away_team = m.get("awayTeam", {}).get("teamNameCH", "")
                match_date = m.get("matchDate", "")[:16].replace("T", " ")
                
                had = m.get("hadodds", {})
                h_odds = had.get("H", "").split("@")[-1]
                d_odds = had.get("D", "").split("@")[-1]
                a_odds = had.get("A", "").split("@")[-1]
                
                if home_team and away_team:
                    matches_list.append({
                        "球賽編號": f"FB{match_id}" if match_id and not str(match_id).startswith("FB") else match_id,
                        "聯賽": league,
                        "主隊": home_team,
                        "客隊": away_team,
                        "開賽時間": match_date,
                        "主勝(H)": float(h_odds) if h_odds else None,
                        "和局(D)": float(d_odds) if d_odds else None,
                        "客勝(A)": float(a_odds) if a_odds else None
                    })
            if matches_list:
                return pd.DataFrame(matches_list)
    except Exception as e:
        print(f"抓取失敗: {e}")
        
    return pd.DataFrame([{
        "球賽編號": "無開盤",
        "聯賽": "連線失敗",
        "主隊": "無資料",
        "客隊": "無資料",
        "開賽時間": "-",
        "主勝(H)": None,
        "和局(D)": None,
        "客勝(A)": None
    }])

# 1. 執行數據抓取並生成 Excel
df = fetch_hkjc_odds()
file_name = "hkjc_daily_odds.xlsx"
df.to_excel(file_name, index=False)

# 2. 調用 Gemini API 生成 Threads 引流文案
gemini_api_key = os.environ.get("GEMINI_API_KEY")
threads_post = "（無法生成文案，請檢查 GEMINI_API_KEY）"

if gemini_api_key and not df.empty and df.iloc[0]["球賽編號"] != "無開盤":
    sample_data = df.head(8).to_string(index=False)
    
    prompt = f"""
    你是一位精通香港馬會足智彩大數據的 Threads 營運專家。
    請根據以下馬會最新即時賠率數據，寫一篇 150-200 字專屬 Threads 的高吸引力貼文：

    {sample_data}

    要求：
    1. 開頭用「今日馬會最新賠率大數據已更新！」等具備震撼力的句子吸睛。
    2. 挑選 1-2 場熱門或賠率懸殊/有冷門潛力的賽事進行點評。
    3. 語氣使用香港廣東話（口語化、貼地、專業），並加入適當足球與數據 Emoji。
    4. 結尾強烈引流：「想獲取每日完整馬會賠率 Excel 與大數據分析？即刻點擊 Bio 連結加入 Discord VIP 頻道！」。
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            threads_post = res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API 調用失敗: {e}")

# 3. 推送結果至 Discord Webhook
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    requests.post(webhook_url, data={"content": f"📝 **【今日 Threads 引流文案草稿】**\n\n{threads_post}"})
    with open(file_name, "rb") as f:
        requests.post(
            webhook_url,
            data={"content": "⚽ **【香港馬會足智彩】最新即時賽程與賠率 Excel 已生成！**"},
            files={"file": f}
        )
import os
import requests
import pandas as pd

def fetch_hkjc_odds():
    """模擬真實瀏覽器抓取馬會即時賠率"""
    url = "https://bet.hkjc.com/football/getJSON.aspx?jsontype=odds_had.aspx"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://bet.hkjc.com/ch/football/home",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # 先訪問主頁獲取 Cookie 繞過阻擋
        session.get("https://bet.hkjc.com/ch/football/home", timeout=10)
        res = session.get(url, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            matches = data.get("matches", [])
            matches_list = []
            
            for m in matches:
                match_id = m.get("bno", m.get("matchNum", ""))
                league = m.get("league", {}).get("leagueNameCH", "")
                home_team = m.get("homeTeam", {}).get("teamNameCH", "")
                away_team = m.get("awayTeam", {}).get("teamNameCH", "")
                match_date = m.get("matchDate", "")[:16].replace("T", " ")
                
                had = m.get("hadodds", {})
                h_odds = had.get("H", "").split("@")[-1]
                d_odds = had.get("D", "").split("@")[-1]
                a_odds = had.get("A", "").split("@")[-1]
                
                if home_team and away_team:
                    matches_list.append({
                        "球賽編號": f"FB{match_id}" if match_id and not str(match_id).startswith("FB") else match_id,
                        "聯賽": league,
                        "主隊": home_team,
                        "客隊": away_team,
                        "開賽時間": match_date,
                        "主勝(H)": float(h_odds) if h_odds else None,
                        "和局(D)": float(d_odds) if d_odds else None,
                        "客勝(A)": float(a_odds) if a_odds else None
                    })
            if matches_list:
                return pd.DataFrame(matches_list)
    except Exception as e:
        print(f"抓取失敗: {e}")
        
    return pd.DataFrame([{
        "球賽編號": "無開盤",
        "聯賽": "連線失敗",
        "主隊": "無資料",
        "客隊": "無資料",
        "開賽時間": "-",
        "主勝(H)": None,
        "和局(D)": None,
        "客勝(A)": None
    }])

# 1. 執行數據抓取並生成 Excel
df = fetch_hkjc_odds()
file_name = "hkjc_daily_odds.xlsx"
df.to_excel(file_name, index=False)

# 2. 調用 Gemini API 生成 Threads 引流文案
gemini_api_key = os.environ.get("GEMINI_API_KEY")
threads_post = "（無法生成文案，請檢查 GEMINI_API_KEY）"

if gemini_api_key and not df.empty and df.iloc[0]["球賽編號"] != "無開盤":
    sample_data = df.head(8).to_string(index=False)
    
    prompt = f"""
    你是一位精通香港馬會足智彩大數據的 Threads 營運專家。
    請根據以下馬會最新即時賠率數據，寫一篇 150-200 字專屬 Threads 的高吸引力貼文：

    {sample_data}

    要求：
    1. 開頭用「今日馬會最新賠率大數據已更新！」等具備震撼力的句子吸睛。
    2. 挑選 1-2 場熱門或賠率懸殊/有冷門潛力的賽事進行點評。
    3. 語氣使用香港廣東話（口語化、貼地、專業），並加入適當足球與數據 Emoji。
    4. 結尾強烈引流：「想獲取每日完整馬會賠率 Excel 與大數據分析？即刻點擊 Bio 連結加入 Discord VIP 頻道！」。
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            threads_post = res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API 調用失敗: {e}")

# 3. 推送結果至 Discord Webhook
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    requests.post(webhook_url, data={"content": f"📝 **【今日 Threads 引流文案草稿】**\n\n{threads_post}"})
    with open(file_name, "rb") as f:
        requests.post(
            webhook_url,
            data={"content": "⚽ **【香港馬會足智彩】最新即時賽程與賠率 Excel 已生成！**"},
            files={"file": f}
        )

