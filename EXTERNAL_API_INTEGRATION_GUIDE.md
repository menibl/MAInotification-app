# מדריך אינטגרציה עם API חיצוני

## סקירה כללית

המערכת עכשיו יכולה לסנכרן נתונים אוטומטית מה-API החיצוני שלך:
- משימות (Missions)
- מצלמות (Cameras)
- נתוני GPS
- סטטוס מצלמות

---

## שלב 1: הגדרת ה-API החיצוני

### ערוך את קובץ .env

```bash
nano /app/backend/.env
```

### שנה את השורה:
```bash
# מ:
EXTERNAL_API_URL="http://your-api-url-here.com/api"

# ל: (כתובת ה-API שלך)
EXTERNAL_API_URL="https://your-actual-api.com/api"
```

**דוגמה:**
```bash
EXTERNAL_API_URL="https://api.maifocus.com/v1"
```

### שמור והפעל מחדש:
```bash
sudo supervisorctl restart backend
```

---

## שלב 2: המבנה של ה-API החיצוני

הקוד מצפה ל-endpoints הבאים ב-API החיצוני:

### 1. קבלת User ID מאימייל
```
GET /user/by-email?email={user_email}
```

**Response צפוי:**
```json
{
  "_id": "user-external-id-123",
  "email": "user@example.com",
  "phone": "050-1234567"
}
```

### 2. קבלת משימות
```
GET /missions?user_id={external_user_id}
```

**Response צפוי:**
```json
[
  {
    "_id": "mission-external-id-1",
    "name": "אבטחת כניסות",
    "description": "ניטור כל הכניסות",
    "cameraIds": ["camera-1", "camera-2"],
    "status": "active",
    "createdBy": "user-external-id-123"
  }
]
```

### 3. קבלת מצלמות
```
GET /cameras?user_id={external_user_id}
```

**Response צפוי:**
```json
[
  {
    "_id": "camera-external-id-1",
    "name": "מצלמה כניסה ראשית",
    "type": "camera",
    "streamUrl": "https://stream.example.com/live",
    "rtmpCode": "rtmp://stream.example.com/live/key123",
    "streamStatus": "active",
    "location": "שער כניסה ראשי"
  }
]
```

### 4. קבלת GPS (אופציונלי)
```
GET /polygons?camera_id={camera_id}
```

**Response צפוי:**
```json
{
  "camera_id": "camera-external-id-1",
  "polygon_coords": [
    {"lat": 32.0853, "lng": 34.7818},
    {"lat": 32.0854, "lng": 34.7819}
  ]
}
```

---

## שלב 3: שימוש ב-Sync API

### בדיקת סטטוס
```bash
curl -X GET "https://aidevicechat.preview.emergentagent.com/api/sync/status"
```

**Response:**
```json
{
  "external_api_configured": true,
  "external_api_url": "https://your-api.com/api",
  "sync_available": true,
  "instructions": "Set EXTERNAL_API_URL in backend/.env file to enable sync"
}
```

### ביצוע סנכרון ידני
```bash
curl -X POST "https://aidevicechat.preview.emergentagent.com/api/sync/from-external?user_email=menibl1111@gmail.com"
```

**Response הצלחה:**
```json
{
  "success": true,
  "user_email": "menibl1111@gmail.com",
  "missions_synced": 3,
  "cameras_synced": 6,
  "errors": [],
  "timestamp": "2025-01-09T15:30:00"
}
```

**Response עם שגיאות:**
```json
{
  "success": true,
  "user_email": "menibl1111@gmail.com",
  "missions_synced": 3,
  "cameras_synced": 5,
  "errors": [
    "GPS sync error for camera-1: Connection timeout"
  ],
  "timestamp": "2025-01-09T15:30:00"
}
```

---

## שלב 4: המרת נתונים

### מה קורה בסנכרון?

#### Missions
```
External System        →        Our System
================              ================
_id                   →        id
name                  →        name
description           →        description
cameraIds             →        camera_ids
createdBy             →        (ignored, use user_email)
                               user_id (from email)
                               created_at (auto)
                               updated_at (auto)
```

#### Cameras
```
External System        →        Our System
================              ================
_id                   →        id
name                  →        name
type                  →        type
streamUrl             →        settings.live_stream_url
rtmpCode              →        settings.rtmp_code
streamStatus          →        status (active=online)
location              →        location
                               user_id (from email)
                               gps_* (from polygons)
                               created_at (auto)
                               updated_at (auto)
```

#### GPS
```
External System        →        Our System
================              ================
polygon_coords[0].lat →        gps_latitude
polygon_coords[0].lng →        gps_longitude
(none)                →        gps_altitude (null)
(auto)                →        gps_updated_at
```

---

## שלב 5: סנכרון אוטומטי (כל דקה)

### אופציה 1: Cron Job (Linux)

ערוך crontab:
```bash
crontab -e
```

הוסף שורה:
```bash
# Sync data every minute
* * * * * curl -X POST "https://aidevicechat.preview.emergentagent.com/api/sync/from-external?user_email=menibl1111@gmail.com" >> /var/log/sync.log 2>&1
```

### אופציה 2: Python Script

צור קובץ `/app/backend/sync_scheduler.py`:

```python
import asyncio
import httpx
import os
from datetime import datetime

API_URL = "https://aidevicechat.preview.emergentagent.com/api"
USER_EMAIL = "menibl1111@gmail.com"

async def sync_data():
    """Run sync every minute"""
    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{API_URL}/sync/from-external",
                    params={"user_email": USER_EMAIL}
                )
                result = response.json()
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if result.get('success'):
                    print(f"[{timestamp}] ✅ Sync success: "
                          f"{result.get('missions_synced')} missions, "
                          f"{result.get('cameras_synced')} cameras")
                else:
                    print(f"[{timestamp}] ❌ Sync failed: {result.get('error')}")
                    
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️ Sync error: {e}")
        
        # Wait 60 seconds
        await asyncio.sleep(60)

if __name__ == "__main__":
    print("🚀 Starting sync scheduler (every 60 seconds)...")
    asyncio.run(sync_data())
```

הרץ ברקע:
```bash
nohup python /app/backend/sync_scheduler.py > /var/log/sync_scheduler.log 2>&1 &
```

### אופציה 3: Systemd Service

צור `/etc/systemd/system/sync-scheduler.service`:

```ini
[Unit]
Description=Data Sync Scheduler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/app/backend
ExecStart=/usr/bin/python3 /app/backend/sync_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

הפעל:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sync-scheduler
sudo systemctl start sync-scheduler
sudo systemctl status sync-scheduler
```

---

## בדיקה ואימות

### 1. בדוק שה-API מוגדר
```bash
curl -s "https://aidevicechat.preview.emergentagent.com/api/sync/status" | jq '.'
```

צפוי:
```json
{
  "external_api_configured": true,
  "external_api_url": "https://your-api.com/api",
  "sync_available": true
}
```

### 2. בצע סנכרון ידני
```bash
curl -X POST "https://aidevicechat.preview.emergentagent.com/api/sync/from-external?user_email=menibl1111@gmail.com" | jq '.'
```

### 3. בדוק שהנתונים הגיעו

**בדוק משימות:**
```bash
curl -s "https://aidevicechat.preview.emergentagent.com/api/missions/menibl1111@gmail.com" | jq 'length'
```

**בדוק מצלמות:**
```bash
curl -s "https://aidevicechat.preview.emergentagent.com/api/devices/menibl1111@gmail.com" | jq 'length'
```

**בדוק GPS:**
```bash
curl -s "https://aidevicechat.preview.emergentagent.com/api/devices/menibl1111@gmail.com" | jq '.[] | select(.gps_latitude != null) | {name, gps_latitude, gps_longitude}'
```

---

## טיפול בשגיאות

### שגיאה: "External API URL not configured"
**פתרון:** ערוך `/app/backend/.env` והגדר `EXTERNAL_API_URL`

### שגיאה: "User not found in external system"
**פתרון:** וודא שהמשתמש קיים ב-API החיצוני עם אותו email

### שגיאה: "Failed to get user from external API: Connection refused"
**פתרון:** 
- בדוק שה-URL נכון
- בדוק שה-API החיצוני רץ
- בדוק חיבור רשת

### שגיאה: "Missions sync error: 404 Not Found"
**פתרון:** ה-endpoint `/missions` לא קיים ב-API החיצוני

---

## התאמת הקוד לצרכים שלך

אם המבנה של ה-API שלך שונה, ערוך את הקוד ב-`/app/backend/server.py`:

### לדוגמה: שינוי endpoint של משימות

מצא:
```python
missions_response = await client.get(f"{external_api_url}/missions", params={"user_id": external_user_id})
```

שנה ל:
```python
missions_response = await client.get(f"{external_api_url}/user/{external_user_id}/missions")
```

### לדוגמה: שינוי מיפוי שדות

מצא:
```python
mission_data = {
    "name": ext_mission.get('name', 'Unnamed Mission'),
    ...
}
```

שנה ל:
```python
mission_data = {
    "name": ext_mission.get('missionName', 'Unnamed Mission'),  # שם שדה שונה
    ...
}
```

---

## לוג וניטור

### צפה בלוגים של הסנכרון
```bash
# Cron logs
tail -f /var/log/sync.log

# Scheduler logs
tail -f /var/log/sync_scheduler.log

# Backend logs
sudo supervisorctl tail -f backend
```

### מבנה לוג צפוי
```
[2025-01-09 15:30:00] ✅ Sync success: 3 missions, 6 cameras
[2025-01-09 15:31:00] ✅ Sync success: 3 missions, 6 cameras
[2025-01-09 15:32:00] ⚠️ Sync error: Connection timeout
[2025-01-09 15:33:00] ✅ Sync success: 3 missions, 6 cameras
```

---

## סיכום - Checklist

- [ ] הגדרתי את `EXTERNAL_API_URL` ב-`.env`
- [ ] בדקתי את סטטוס הסנכרון (`/sync/status`)
- [ ] הרצתי סנכרון ידני ראשון בהצלחה
- [ ] הנתונים מופיעים באפליקציה
- [ ] GPS עובד (אם רלוונטי)
- [ ] הגדרתי סנכרון אוטומטי (cron/scheduler/systemd)
- [ ] בדקתי שהסנכרון האוטומטי רץ

---

## תמיכה

אם משהו לא עובד:

1. **בדוק logs:**
   ```bash
   sudo supervisorctl tail -f backend
   ```

2. **בדוק את ה-.env:**
   ```bash
   cat /app/backend/.env | grep EXTERNAL_API_URL
   ```

3. **בדוק חיבור ל-API החיצוני:**
   ```bash
   curl -I https://your-external-api.com/api/status
   ```

4. **בצע sync ידני ובדוק את ה-response:**
   ```bash
   curl -X POST "https://aidevicechat.preview.emergentagent.com/api/sync/from-external?user_email=YOUR_EMAIL" | jq '.'
   ```

---

## הערות חשובות

1. **אבטחה:** אם ה-API החיצוני דורש authentication, תצטרך להוסיף headers (API key, Bearer token)

2. **Rate Limiting:** אם ה-API החיצוני מוגבל ב-requests, שקול להפחית תדירות

3. **Performance:** סנכרון של מאות מצלמות יכול לקחת זמן - שקול paging/batching

4. **Idempotency:** הקוד תומך ב-upsert - אפשר להריץ כמה פעמים בלי בעיה

5. **GPS:** GPS הוא אופציונלי - המערכת תמשיך לעבוד גם בלי GPS
