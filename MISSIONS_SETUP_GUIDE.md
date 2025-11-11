# מדריך הגדרת משימות ומצלמות

## מה חדש בשלב 2 ✅

### תצוגת משימות משופרת
- 📁 קיבוץ מצלמות לפי משימות
- 🔤 מיון משימות לפי א-ב (עברית ואנגלית)
- 📊 הצגת מספר מצלמות בכל משימה
- 📂 פתיחה/סגירה של משימות (Expandable)
- 📋 קבוצת "Unassigned Cameras" למצלמות ללא משימה
- 🔍 ניווט מהיר למצלמות

---

## הגדרה ראשונית - דוגמה מלאה

### שלב 1: יצירת 6 מצלמות עם GPS

```bash
API_URL="https://mission-control-pwa.preview.emergentagent.com/api"
USER_EMAIL="menibl1111@gmail.com"

# מצלמה 1 - כניסה ראשית
curl -X POST "$API_URL/devices" -H 'Content-Type: application/json' -d '{
  "name": "מצלמה כניסה ראשית",
  "type": "camera",
  "user_id": "'$USER_EMAIL'",
  "location": "שער כניסה ראשי",
  "gps_latitude": 32.0853,
  "gps_longitude": 34.7818
}'

echo "מצלמה 1 נוצרה"
sleep 1

# מצלמה 2 - כניסה אחורית
curl -X POST "$API_URL/devices" -H 'Content-Type: application/json' -d '{
  "name": "מצלמה כניסה אחורית",
  "type": "camera",
  "user_id": "'$USER_EMAIL'",
  "location": "שער אחורי",
  "gps_latitude": 32.0843,
  "gps_longitude": 34.7828
}'

echo "מצלמה 2 נוצרה"
sleep 1

# מצלמה 3 - חניון קומה 1
curl -X POST "$API_URL/devices" -H 'Content-Type: application/json' -d '{
  "name": "מצלמת חניון 1",
  "type": "camera",
  "user_id": "'$USER_EMAIL'",
  "location": "חניון תת קרקעי קומה 1",
  "gps_latitude": 32.0860,
  "gps_longitude": 34.7810
}'

echo "מצלמה 3 נוצרה"
sleep 1

# מצלמה 4 - חניון קומה 2
curl -X POST "$API_URL/devices" -H 'Content-Type: application/json' -d '{
  "name": "מצלמת חניון 2",
  "type": "camera",
  "user_id": "'$USER_EMAIL'",
  "location": "חניון תת קרקעי קומה 2",
  "gps_latitude": 32.0862,
  "gps_longitude": 34.7812
}'

echo "מצלמה 4 נוצרה"
sleep 1

# מצלמה 5 - לובי
curl -X POST "$API_URL/devices" -H 'Content-Type: application/json' -d '{
  "name": "מצלמת לובי",
  "type": "camera",
  "user_id": "'$USER_EMAIL'",
  "location": "לובי ראשי",
  "gps_latitude": 32.0855,
  "gps_longitude": 34.7820
}'

echo "מצלמה 5 נוצרה"
sleep 1

# מצלמה 6 - גג
curl -X POST "$API_URL/devices" -H 'Content-Type: application/json' -d '{
  "name": "מצלמת גג",
  "type": "camera",
  "user_id": "'$USER_EMAIL'",
  "location": "גג הבניין",
  "gps_latitude": 32.0857,
  "gps_longitude": 34.7822,
  "gps_altitude": 50
}'

echo "✅ 6 מצלמות נוצרו בהצלחה!"
```

---

### שלב 2: שמור את IDs של המצלמות

```bash
# קבל רשימת מצלמות
curl -s "$API_URL/devices/$USER_EMAIL" | jq -r '.[] | "\(.id) - \(.name)"'
```

**העתק את ה-IDs שקיבלת לכאן:**
```
CAMERA_1_ID="..."  # כניסה ראשית
CAMERA_2_ID="..."  # כניסה אחורית
CAMERA_3_ID="..."  # חניון 1
CAMERA_4_ID="..."  # חניון 2
CAMERA_5_ID="..."  # לובי
CAMERA_6_ID="..."  # גג
```

---

### שלב 3: יצירת 3 משימות

```bash
# משימה 1: אבטחת כניסות
MISSION_1=$(curl -s -X POST "$API_URL/missions?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
  "name": "אבטחת כניסות",
  "description": "ניטור כל הכניסות לבניין",
  "camera_ids": []
}' | jq -r '.mission_id')

echo "משימה 1 נוצרה: $MISSION_1"
sleep 1

# משימה 2: ניטור חניון
MISSION_2=$(curl -s -X POST "$API_URL/missions?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
  "name": "ניטור חניון",
  "description": "ניטור חניון תת קרקעי",
  "camera_ids": []
}' | jq -r '.mission_id')

echo "משימה 2 נוצרה: $MISSION_2"
sleep 1

# משימה 3: שמירה מקיפה
MISSION_3=$(curl -s -X POST "$API_URL/missions?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{
  "name": "שמירה מקיפה",
  "description": "ניטור כללי של הבניין",
  "camera_ids": []
}' | jq -r '.mission_id')

echo "משימה 3 נוצרה: $MISSION_3"
echo "✅ 3 משימות נוצרו בהצלחה!"
```

---

### שלב 4: חיבור מצלמות למשימות

```bash
# חבר מצלמות למשימה 1: אבטחת כניסות (כניסה ראשית + אחורית + לובי)
curl -X POST "$API_URL/missions/assign-cameras" \
-H 'Content-Type: application/json' \
-d '{
  "user_id": "'$USER_EMAIL'",
  "mission_id": "'$MISSION_1'",
  "camera_ids": ["'$CAMERA_1_ID'", "'$CAMERA_2_ID'", "'$CAMERA_5_ID'"]
}'

echo "✅ 3 מצלמות חוברו למשימה 1"
sleep 1

# חבר מצלמות למשימה 2: ניטור חניון (חניון 1 + חניון 2)
curl -X POST "$API_URL/missions/assign-cameras" \
-H 'Content-Type: application/json' \
-d '{
  "user_id": "'$USER_EMAIL'",
  "mission_id": "'$MISSION_2'",
  "camera_ids": ["'$CAMERA_3_ID'", "'$CAMERA_4_ID'"]
}'

echo "✅ 2 מצלמות חוברו למשימה 2"
sleep 1

# השאר מצלמה אחת (גג) ללא משימה - תופיע ב-"Unassigned"

echo "✅ הגדרה הושלמה בהצלחה!"
```

---

## איך זה נראה בממשק

### תצוגת רשימה (List)
```
📁 אבטחת כניסות                    (3 cameras)     ▶
📁 ניטור חניון                     (2 cameras)     ▶
📁 שמירה מקיפה                     (0 cameras)     ▶
📁 Unassigned Cameras              (1 cameras)     ▶
```

### לאחר פתיחת "אבטחת כניסות"
```
📂 אבטחת כניסות                    (3 cameras)     ▼
    🟢 מצלמה כניסה ראשית
        שער כניסה ראשי
    🟢 מצלמה כניסה אחורית
        שער אחורי
    🟢 מצלמת לובי
        לובי ראשי

📁 ניטור חניון                     (2 cameras)     ▶
📁 שמירה מקיפה                     (0 cameras)     ▶
📁 Unassigned Cameras              (1 cameras)     ▶
```

---

## Curl Commands שימושיים

### קבל את כל המצלמות
```bash
curl -s "$API_URL/devices/$USER_EMAIL" | jq '.'
```

### קבל את כל המשימות
```bash
curl -s "$API_URL/missions/$USER_EMAIL" | jq '.'
```

### קבל משימה ספציפית
```bash
curl -s "$API_URL/missions/$USER_EMAIL" | jq '.[] | select(.name == "אבטחת כניסות")'
```

### הוסף מצלמה למשימה קיימת
```bash
# קודם קבל את רשימת המצלמות הנוכחית
CURRENT_CAMERAS=$(curl -s "$API_URL/missions/$USER_EMAIL" | jq -r '.[] | select(.id == "'$MISSION_1'") | .camera_ids | @json')

# הוסף מצלמה נוספת
curl -X POST "$API_URL/missions/assign-cameras" \
-H 'Content-Type: application/json' \
-d '{
  "user_id": "'$USER_EMAIL'",
  "mission_id": "'$MISSION_1'",
  "camera_ids": ['$CURRENT_CAMERAS', "'$CAMERA_6_ID'"]
}'
```

### הסר מצלמה ממשימה
```bash
# עדכן את רשימת המצלמות ללא המצלמה שרוצים להסיר
curl -X POST "$API_URL/missions/assign-cameras" \
-H 'Content-Type: application/json' \
-d '{
  "user_id": "'$USER_EMAIL'",
  "mission_id": "'$MISSION_1'",
  "camera_ids": ["'$CAMERA_1_ID'", "'$CAMERA_2_ID'"]
}'
```

---

## מבנה הנתונים

### Mission
```json
{
  "id": "mission-abc123",
  "user_id": "menibl1111@gmail.com",
  "name": "אבטחת כניסות",
  "description": "ניטור כל הכניסות לבניין",
  "camera_ids": [
    "camera-1-id",
    "camera-2-id",
    "camera-3-id"
  ],
  "created_at": "2025-01-09T14:00:00Z",
  "updated_at": "2025-01-09T14:30:00Z"
}
```

### Device (Camera)
```json
{
  "id": "camera-1-id",
  "name": "מצלמה כניסה ראשית",
  "type": "camera",
  "user_id": "menibl1111@gmail.com",
  "status": "online",
  "location": "שער כניסה ראשי",
  "gps_latitude": 32.0853,
  "gps_longitude": 34.7818,
  "gps_altitude": 10.5
}
```

---

## תכונות נוספות

### 1. מיון אוטומטי
- משימות ממוינות א-ב באופן אוטומטי
- תומך בעברית ואנגלית

### 2. סטטוס Visual
- 🟢 ירוק = online
- ⚪ אפור = offline

### 3. ניווט מהיר
- לחיצה על משימה = פותח/סוגר
- לחיצה על מצלמה = פותח צ'אט

### 4. מידע חזותי
- מספר מצלמות בכל משימה
- סמלים ברורים (📁/📂)
- צבעים ושקיפות

---

## בעיות נפוצות ופתרונות

### בעיה: משימות לא נטענות
**פתרון:**
```bash
# בדוק שיש משימות
curl -s "$API_URL/missions/$USER_EMAIL" | jq 'length'

# אם 0 - יצור משימה
```

### בעיה: מצלמות לא מופיעות במשימה
**פתרון:**
```bash
# בדוק שה-camera_ids נכונים
curl -s "$API_URL/missions/$USER_EMAIL" | jq '.[] | {name, camera_ids}'

# בדוק שהמצלמות קיימות
curl -s "$API_URL/devices/$USER_EMAIL" | jq '.[] | .id'
```

### בעיה: כל המצלמות ב-"Unassigned"
**פתרון:**
```bash
# חבר אותן למשימות דרך assign-cameras API
```

---

## סקריפט אוטומטי - Setup מלא

שמור את זה כ-`setup_missions.sh`:

```bash
#!/bin/bash

API_URL="https://mission-control-pwa.preview.emergentagent.com/api"
USER_EMAIL="menibl1111@gmail.com"

echo "🚀 Starting missions setup..."

# Create cameras
echo "📹 Creating cameras..."
CAMERA_IDS=()

for i in {1..6}; do
  RESPONSE=$(curl -s -X POST "$API_URL/devices" -H 'Content-Type: application/json' -d '{
    "name": "Camera '$i'",
    "type": "camera",
    "user_id": "'$USER_EMAIL'",
    "gps_latitude": '$(echo "32.0850 + $i * 0.001" | bc)',
    "gps_longitude": 34.7818
  }')
  
  CAMERA_ID=$(echo $RESPONSE | jq -r '.id')
  CAMERA_IDS+=($CAMERA_ID)
  echo "  ✅ Camera $i: $CAMERA_ID"
  sleep 0.5
done

# Create missions
echo "📋 Creating missions..."
MISSION_1=$(curl -s -X POST "$API_URL/missions?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{"name":"Mission Alpha","description":"First mission","camera_ids":[]}' \
| jq -r '.mission_id')

MISSION_2=$(curl -s -X POST "$API_URL/missions?user_id=$USER_EMAIL" \
-H 'Content-Type: application/json' \
-d '{"name":"Mission Beta","description":"Second mission","camera_ids":[]}' \
| jq -r '.mission_id')

echo "  ✅ Mission Alpha: $MISSION_1"
echo "  ✅ Mission Beta: $MISSION_2"

# Assign cameras
echo "🔗 Assigning cameras to missions..."
curl -s -X POST "$API_URL/missions/assign-cameras" \
-H 'Content-Type: application/json' \
-d '{
  "user_id": "'$USER_EMAIL'",
  "mission_id": "'$MISSION_1'",
  "camera_ids": ["'${CAMERA_IDS[0]}'", "'${CAMERA_IDS[1]}'", "'${CAMERA_IDS[2]}'"]
}' > /dev/null

curl -s -X POST "$API_URL/missions/assign-cameras" \
-H 'Content-Type: application/json' \
-d '{
  "user_id": "'$USER_EMAIL'",
  "mission_id": "'$MISSION_2'",
  "camera_ids": ["'${CAMERA_IDS[3]}'", "'${CAMERA_IDS[4]}'"]
}' > /dev/null

echo "  ✅ Cameras assigned"
echo ""
echo "✨ Setup complete!"
echo "📱 Open the app and check the 'List' tab"
echo ""
echo "Summary:"
echo "  - 6 cameras created"
echo "  - 2 missions created"
echo "  - Mission Alpha: 3 cameras"
echo "  - Mission Beta: 2 cameras"
echo "  - Unassigned: 1 camera"
```

**הרצה:**
```bash
chmod +x setup_missions.sh
./setup_missions.sh
```

---

## סיכום

✅ **תצוגת משימות משופרת**
- קיבוץ מצלמות לפי משימות
- מיון א-ב אוטומטי
- פתיחה/סגירה של משימות
- Unassigned cameras

🎯 **השלב הבא (שלב 3):**
- אינטגרציה עם API החיצוני
- סנכרון אוטומטי כל דקה
- המרת נתונים למבנה שלנו
