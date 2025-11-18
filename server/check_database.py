#!/usr/bin/env python3
"""
Diagnostic script to check database state for limit enforcement debugging.
"""
import sqlite3
from datetime import datetime

# Connect to database
db_path = "bobavision.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("BOBAVISION DATABASE DIAGNOSTIC")
print("=" * 70)

# Check client settings
print("\n1. CLIENT SETTINGS")
print("-" * 70)
cursor.execute("SELECT client_id, friendly_name, daily_limit FROM client_settings")
clients = cursor.fetchall()
if clients:
    for client in clients:
        print(f"  Client ID: {client[0]}")
        print(f"  Name: {client[1]}")
        print(f"  Daily Limit: {client[2]}")
        print()
else:
    print("  ⚠️  No clients in database (will use default limit of 3)")

# Check videos
print("\n2. VIDEOS IN DATABASE")
print("-" * 70)
cursor.execute("SELECT COUNT(*) FROM videos WHERE is_placeholder = 0")
real_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM videos WHERE is_placeholder = 1")
placeholder_count = cursor.fetchone()[0]
print(f"  Real videos: {real_count}")
print(f"  Placeholder videos: {placeholder_count}")

if placeholder_count == 0:
    print("\n  ⚠️  CRITICAL: No placeholder videos!")
    print("  Without placeholder videos, limits cannot be enforced.")
    print("  Add a video with 'placeholder' in the filename and scan.")

# Show sample videos
print("\n  Sample videos:")
cursor.execute("SELECT id, title, is_placeholder FROM videos LIMIT 5")
for vid in cursor.fetchall():
    placeholder_flag = "PLACEHOLDER" if vid[2] else "REAL"
    print(f"    [{vid[0]}] {vid[1]} ({placeholder_flag})")

# Check today's play log
print("\n3. PLAY LOG FOR TODAY")
print("-" * 70)
cursor.execute("""
    SELECT client_id, COUNT(*) as total_plays,
           SUM(CASE WHEN is_placeholder = 0 THEN 1 ELSE 0 END) as real_plays,
           SUM(CASE WHEN is_placeholder = 1 THEN 1 ELSE 0 END) as placeholder_plays
    FROM play_log
    WHERE date(played_at) = date('now')
    GROUP BY client_id
""")
play_stats = cursor.fetchall()

if play_stats:
    for stats in play_stats:
        print(f"  Client: {stats[0]}")
        print(f"    Total plays: {stats[1]}")
        print(f"    Real videos: {stats[2]}")
        print(f"    Placeholders: {stats[3]}")
        print()
else:
    print("  No plays logged for today")

# Check recent plays for local-test-client
print("\n4. RECENT PLAYS FOR 'local-test-client'")
print("-" * 70)
cursor.execute("""
    SELECT p.id, p.played_at, p.is_placeholder, v.title
    FROM play_log p
    JOIN videos v ON p.video_id = v.id
    WHERE p.client_id = 'local-test-client'
    ORDER BY p.played_at DESC
    LIMIT 10
""")
recent_plays = cursor.fetchall()
if recent_plays:
    for play in recent_plays:
        placeholder_flag = "PLACEHOLDER" if play[2] else "REAL"
        print(f"  [{play[0]}] {play[1]} - {play[3]} ({placeholder_flag})")
else:
    print("  No plays found for 'local-test-client'")

# Check if limit should be enforced now
print("\n5. LIMIT ENFORCEMENT STATUS")
print("-" * 70)
cursor.execute("""
    SELECT daily_limit FROM client_settings WHERE client_id = 'local-test-client'
""")
limit_result = cursor.fetchone()
daily_limit = limit_result[0] if limit_result else 3

cursor.execute("""
    SELECT COUNT(*) FROM play_log
    WHERE client_id = 'local-test-client'
    AND date(played_at) = date('now')
    AND is_placeholder = 0
""")
plays_today = cursor.fetchone()[0]

print(f"  Daily Limit: {daily_limit}")
print(f"  Real videos played today: {plays_today}")
print(f"  Limit reached: {'YES' if plays_today >= daily_limit else 'NO'}")

if plays_today >= daily_limit and placeholder_count == 0:
    print("\n  ⚠️  PROBLEM DETECTED:")
    print("  Limit is reached but there are no placeholder videos!")
    print("  The system will fail to enforce the limit.")

conn.close()

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
