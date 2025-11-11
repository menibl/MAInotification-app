# מדריך GPS ותצוגת מפה

## מה נוסף

### 1. שדות GPS במודל Device ✅

כל מצלמה/אמצעי יכולה עכשיו לכלול:
- `gps_latitude` - קו רוחב (latitude)
- `gps_longitude` - קו אורך (longitude)  
- `gps_altitude` - גובה במטרים (אופציונלי)
- `gps_updated_at` - מתי ה-GPS עודכן לאחרונה

### 2. API Endpoints חדשים ✅

#### עדכון GPS למצלמה
```bash
curl -X PUT "$API_URL/devices/{device_id}/gps?latitude=32.0853&longitude=34.7818&altitude=10"
```

#### יצירת מצלמה עם GPS
```bash
curl -X POST "$API_URL/devices" \
-H 'Content-Type: application/json' \
-d '{
    "name": "מצלמה כניסה",
    "type": "camera",
    "user_id": "menibl1111@gmail.com",
    "location": "כניסה ראשית",
    "gps_latitude": 32.0853,
    "gps_longitude": 34.7818,
    "gps_altitude": 10
}'
```

#### עדכון GPS דרך Update רגיל
```bash
curl -X PUT "$API_URL/devices/{device_id}" \
-H 'Content-Type: application/json' \
-d '{
    "gps_latitude": 32.0853,
    "gps_longitude": 34.7818,
    "gps_altitude": 10
}'
```

### 3. תצוגת מפה בממשק ✅

**ממשק עם 2 Tabs:**
- 📋 **List** - תצוגת רשימה רגילה (קיימת)
- 🗺️ **Map** - תצוגת מפה חדשה

**תכונות המפה:**
- מציגה את כל המצלמות עם GPS על מפה
- נקודה ירוקה = online
- נקודה אפורה = offline
- לחיצה על נקודה פותחת את הצ'אט
- Popup עם מידע על המצלמה
- Zoom אוטומטי להצגת כל המצלמות

### 4. משתנה .env חדש ✅

בקובץ `/app/backend/.env` נוסף:
```bash
EXTERNAL_API_URL="http://your-api-url-here.com/api"
```

**כאן תזין את כתובת ה-API החיצוני שלך**

---

## דוגמאות שימוש

### דוגמה 1: יצירת מצלמה עם GPS (תל אביב)

```bash
API_URL="https://mission-control-pwa.preview.emergentagent.com/api"

curl -X POST "$API_URL/devices" \
-H 'Content-Type: application/json' \
-d '{
    "name": "מצלמה דיזנגוף",
    "type": "camera",
    "user_id": "menibl1111@gmail.com",
    "location": "רחוב דיזנגוף 100, תל אביב",
    "gps_latitude": 32.0809,
    "gps_longitude": 34.7806,
    "description": "מצלמה במרכז תל אביב"
}'
```

### דוגמה 2: עדכון GPS למצלמה קיימת

```bash
CAMERA_ID="d9325867-371a-4d08-98bd-aeeee866a348"

curl -X PUT "$API_URL/devices/$CAMERA_ID/gps?latitude=32.0853&longitude=34.7818&altitude=15"
```

### דוגמה 3: יצירת מספר מצלמות עם GPS

```bash
#!/bin/bash
API_URL="https://mission-control-pwa.preview.emergentagent.com/api"
USER_EMAIL="menibl1111@gmail.com"

# מצלמה 1 - כניסה צפונית
curl -X POST "$API_URL/devices" \
-H 'Content-Type: application/json' \
-d '{
    "name": "כניסה צפונית",
    "type": "camera",
    "user_id": "'$USER_EMAIL'",
    "location": "שער צפון",
    "gps_latitude": 32.0853,
    "gps_longitude": 34.7818
}'

sleep 1

# מצלמה 2 - כניסה דרומית
curl -X POST "$API_URL/devices" \
-H 'Content-Type: application/json' \
-d '{
    "name": "כניסה דרומית",
    "type": "camera",
    "user_id": "'$USER_EMAIL'",
    "location": "שער דרום",
    "gps_latitude": 32.0843,
    "gps_longitude": 34.7828
}'

sleep 1

# מצלמה 3 - חניון
curl -X POST "$API_URL/devices" \
-H 'Content-Type: application/json' \
-d '{
    "name": "מצלמת חניון",
    "type": "camera",
    "user_id": "'$USER_EMAIL'",
    "location": "חניון ראשי",
    "gps_latitude": 32.0860,
    "gps_longitude": 34.7810
}'

echo "✅ 3 מצלמות עם GPS נוצרו בהצלחה!"
```

---

## מבנה הנתונים

### Device עם GPS

```json
{
  "id": "abc-123",
  "name": "מצלמה כניסה",
  "type": "camera",
  "user_id": "menibl1111@gmail.com",
  "status": "online",
  "location": "כניסה ראשית",
  "description": "מצלמה ראשית",
  
  "gps_latitude": 32.0853,
  "gps_longitude": 34.7818,
  "gps_altitude": 10.5,
  "gps_updated_at": "2025-01-09T14:30:00Z",
  
  "settings": {
    "resolution": "1080p",
    "live_stream_url": "https://stream.example.com"
  },
  
  "last_seen": "2025-01-09T14:35:00Z",
  "created_at": "2025-01-09T10:00:00Z",
  "updated_at": "2025-01-09T14:30:00Z"
}
```

---

## איך להשתמש בממשק

### צעד 1: פתח את האפליקציה
```
https://mission-control-pwa.preview.emergentagent.com
```

### צעד 2: התחבר
```
Email: menibl1111@gmail.com
Password: [הסיסמה שלך]
```

### צעד 3: פתח תפריט מצלמות
לחץ על כפתור התפריט (☰) בצד שמאל למעלה

### צעד 4: עבור לתצוגת מפה
לחץ על הטאב "🗺️ Map" למעלה

### צעד 5: ראה מצלמות על המפה
- כל נקודה = מצלמה
- ירוק = online
- אפור = offline
- לחץ על נקודה לפתיחת צ'אט

---

## קואורדינטות GPS מרכזיות בישראל

### ערים מרכזיות
```javascript
const locations = {
  "תל אביב": { lat: 32.0853, lng: 34.7818 },
  "ירושלים": { lat: 31.7683, lng: 35.2137 },
  "חיפה": { lat: 32.7940, lng: 34.9896 },
  "באר שבע": { lat: 31.2518, lng: 34.7913 },
  "אילת": { lat: 29.5577, lng: 34.9519 },
  "נתניה": { lat: 32.3215, lng: 34.8532 },
  "חולון": { lat: 32.0117, lng: 34.7750 },
  "רמת גן": { lat: 32.0719, lng: 34.8242 }
};
```

---

## הערות חשובות

### 1. פורמט GPS
- **Latitude (קו רוחב):** -90 עד 90
- **Longitude (קו אורך):** -180 עד 180
- **Altitude (גובה):** במטרים מעל פני הים

### 2. דיוק
- GPS יכול להיות עד 7 ספרות אחרי הנקודה
- דוגמה: `32.0853471, 34.7818064`

### 3. מה קורה אם אין GPS?
- המצלמה תופיע ברשימה אבל לא במפה
- ניתן להוסיף GPS מאוחר יותר

### 4. עדכון GPS
- אפשר לעדכן GPS בכל עת
- `gps_updated_at` מתעדכן אוטומטית

---

## שלב הבא - אינטגרציה

לאחר שה-GPS עובד, השלב הבא הוא:

1. **הגדרת URL של API החיצוני**
   ```bash
   # ערוך את הקובץ
   nano /app/backend/.env
   
   # שנה את השורה
   EXTERNAL_API_URL="https://your-actual-api-url.com/api"
   ```

2. **יצירת endpoint לסנכרון**
   - קריאה מה-API החיצוני
   - המרת הנתונים למבנה שלנו
   - שמירה ב-MongoDB

3. **סנכרון אוטומטי כל דקה**
   - Cron job / Background task
   - עדכון GPS, משימות, מצלמות

---

## בדיקה ואימות

### בדוק שה-GPS עובד:

```bash
# קבל את כל המצלמות
curl -s "$API_URL/devices/$USER_EMAIL" | jq '.[] | {name, gps_latitude, gps_longitude}'
```

**תוצאה צפויה:**
```json
{
  "name": "מצלמה כניסה",
  "gps_latitude": 32.0853,
  "gps_longitude": 34.7818
}
```

### בדוק שהמפה עובדת:
1. פתח את האפליקציה
2. לחץ על תפריט המצלמות (☰)
3. לחץ על "🗺️ Map"
4. אתה אמור לראות מפה עם נקודות

---

## תמיכה טכנית

אם משהו לא עובד:

1. **בדוק שהשרת רץ:**
   ```bash
   sudo supervisorctl status
   ```

2. **בדוק לוגים:**
   ```bash
   sudo supervisorctl tail -f backend
   sudo supervisorctl tail -f frontend
   ```

3. **בדוק ש-Leaflet נטען:**
   - פתח Console (F12)
   - הקלד: `window.L`
   - אמור לראות object של Leaflet

---

## סיכום

✅ **מה עובד עכשיו:**
- שדות GPS בכל מצלמה
- API לעדכון GPS
- תצוגת מפה עם Leaflet
- Tabs בין רשימה למפה
- נקודות צבעוניות לפי סטטוס
- Popup עם פרטי המצלמה
- משתנה .env לאינטגרציה עתידית

🔄 **מה הבא:**
- הגדרת URL של API החיצוני
- בניית endpoint לסנכרון נתונים
- סנכרון אוטומטי כל דקה
- שיפור תצוגת משימות
