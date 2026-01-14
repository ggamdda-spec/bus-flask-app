from flask import Flask, render_template, request
import pandas as pd
import os
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
EXCEL_FILE = "버스시간검색(24.01.01).xlsx"

# =========================
# 엑셀 로드
# =========================
df_time = pd.read_excel(
    EXCEL_FILE,
    sheet_name=0,
    header=0
).iloc[:, 0:10]   # A~J열만 강제 사용

df_gps = pd.read_excel(EXCEL_FILE, sheet_name=1)
df_gps.columns = ["정류장명", "위도", "경도"]
df_gps["위도"] = pd.to_numeric(df_gps["위도"], errors="coerce")
df_gps["경도"] = pd.to_numeric(df_gps["경도"], errors="coerce")
df_gps = df_gps.dropna()

# =========================
# 유틸 함수
# =========================
def has_all_values(values):
    return not any(pd.isna(v) or str(v).strip() == "" for v in values)

def format_time(t):
    if isinstance(t, datetime):
        return t.strftime("%H:%M")
    return str(t)[:5]

def time_to_minutes(t):
    try:
        if isinstance(t, datetime):
            return t.hour * 60 + t.minute
        h, m = str(t)[:5].split(":")
        return int(h) * 60 + int(m)
    except:
        return 99999

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def search_station(station):
    up, down = [], []
    key = station.strip()

    if key == "":
        return [], []

    for _, row in df_time.iterrows():
        try:
            up_station = str(row.iloc[0])
            down_station = str(row.iloc[5])
        except:
            continue

        # 상행
        if has_all_values(row.iloc[0:5]) and key in up_station:
            up.append((
                time_to_minutes(row.iloc[1]),
                up_station,
                format_time(row.iloc[1]),
                format_time(row.iloc[2]),
                row.iloc[3],
                row.iloc[4]
            ))

        # 하행
        if has_all_values(row.iloc[5:10]) and key in down_station:
            down.append((
                time_to_minutes(row.iloc[6]),
                down_station,
                format_time(row.iloc[6]),
                format_time(row.iloc[7]),
                row.iloc[8],
                row.iloc[9]
            ))

    return sorted(up), sorted(down)


# =========================
# 메인 페이지
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    station = ""
    up_results = []
    down_results = []

    if request.method == "POST":

        # GPS 검색
        if "lat" in request.form and "lon" in request.form:
            lat = float(request.form["lat"])
            lon = float(request.form["lon"])

            df_gps["거리"] = df_gps.apply(
                lambda r: haversine(lat, lon, r["위도"], r["경도"]),
                axis=1
            )

            nearest = df_gps.sort_values("거리").head(1)
            if not nearest.empty:
                station = nearest.iloc[0]["정류장명"]

        # 수동 검색
        else:
            station = request.form.get("station", "").strip()

        if station != "":
            up_results, down_results = search_station(station)

    return render_template(
        "index.html",
        station=station,
        up_results=up_results,
        down_results=down_results
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

