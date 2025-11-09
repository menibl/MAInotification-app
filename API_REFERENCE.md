# מסמך API מקיף – MAI Focus (Device Chat Platform)

מסמך זה מרכז את כל ה־API הקיימים במערכת, כולל הסברים מלאים, מודלי בקשה/תגובה, הערות תפעול, ודוגמאות curl. המסמך כתוב בעברית, אך שמות השדות באנגלית כפי שהם ב־API.

תוכן עניינים
- בסיס וכתובות – Base URL, כללי שימוש חשובים
- אימות (Auth) ו־Google OAuth + 2FA TOTP
- WebSocket – עדכונים בזמן אמת
- ניהול התקנים (Devices)
- Push Notifications – רישום, שליחה, ביטול, צפייה
- התראות (Notifications) – היסטוריה וסימון נקראו
- צ׳אט (Chat) – שליחת הודעות, היסטוריית צ׳אט, ניתוח תמונה ישיר
- הגדרות AI (Chat Settings) – תפקיד/הוראות + Natural Language Commands
- פרומפט מצלמה (Camera Prompt) – עדכון/פרשנות טבעית/תיקון על בסיס משוב
- קבצים (Files) – העלאה, הורדה, רשימה, מחיקה
- סימולציה – יצירת התראות לדוגמה
- סטטוס ובריאות שירות
- הערות אבטחה, שגיאות נפוצות, ופרקטיקות טובות


בסיס וכתובות – Base URL, כללי שימוש חשובים
- כל ה־Endpoints של backend מתחילים ב־/api
- ה־Frontend חייב להשתמש ב־REACT_APP_BACKEND_URL (אל תקדו כתובות)
- דוגמת Base URL: https://aidevicechat.preview.emergentagent.com
- כל קריאות ה־API: {REACT_APP_BACKEND_URL}/api/...
- חיבור למסד הנתונים (Backend) נעשה באמצעות MONGO_URL מתוך קובץ .env (אסור לקשיח)
- WebSocket: אותו בסיס, עם /api/ws/{user_id}
- הערת Ingress: כל ראוטים חייבים להיות תחת /api


אימות (Auth) ו־Google OAuth + 2FA TOTP
מצב פריסה נוכחי: המערכת נשארת ניתנת לשימוש גם ללא התחברות (Rollout בטוח). כאשר משתמש מחובר – ה־user_id הוא האימייל שב־JWT. בהמשך ניתן להחמיר ולאכוף התחברות לכל הראוטים.

משתני סביבה (Backend/.env):
- JWT_SECRET=your-strong-random-secret
- GOOGLE_CLIENT_ID=...
- GOOGLE_CLIENT_SECRET=...
- OAUTH_GOOGLE_REDIRECT_URI=https://aidevicechat.preview.emergentagent.com/api/oauth/google/callback

ראוטים:
1) POST /api/auth/register
   גוף: { email, password }
   תגובה: { success, token, email } או { success:false, error }
   הערה: סיסמא נשמרת מוצפנת (bcrypt)

2) POST /api/auth/login
   גוף: { email, password }
   תגובה:
   - אם 2FA לא פעיל: { success:true, token, email }
   - אם 2FA פעיל: { success:true, requires_2fa:true, email }

3) POST /api/auth/enable-2fa
   פרמטר: email (query או body)
   תגובה: { otpauth_url, secret }
   הערה: לסריקה ב־Google Authenticator וכד׳

4) POST /api/auth/verify-2fa
   גוף: { email, code }
   תגובה: { success, token, email } או { success:false, error }

5) GET /api/auth/me
   פרמ׳: token (query)
   תשובה: { authenticated:true, email } או { authenticated:false }

6) GET /api/oauth/google/start
   פעולה: מפנה ל־Google OAuth

7) GET /api/oauth/google/callback
   פעולה: החלפת code לטוקן, חילוץ אימייל, רישום/קישור משתמש, החזרה ל־Frontend:
   Redirect ל־/?token=...&email=...

דוגמת curl:
```
curl -X POST "$BACKEND/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"StrongPass123!"}'
```


WebSocket – עדכונים בזמן אמת
- URI: {REACT_APP_BACKEND_URL}/api/ws/{user_id}
- משמש לעדכוני AI, הודעות והתראות בזמן אמת.
- שמרו על Ping תקופתי (הקליינט מבצע).


ניהול התקנים (Devices)
1) POST /api/devices
   גוף: { name, type, user_id, location?, description?, settings? }
   תשובה: Device שנוצר.

2) POST /api/devices/create-with-id
   פרמ׳: device_id,name,type,user_id,location?,description?,settings?,status?
   תשובה: { success, message, device }

3) PUT /api/devices/{old_device_id}/update-id
   פרמ׳: new_device_id, preserve_data=true|false
   תשובה: סיכום מעבר נתונים.

4) GET /api/devices/{user_id}
   תשובה: רשימת התקנים למשתמש.

5) PUT /api/devices/{device_id}
   גוף: { ... } שדות לעדכון, כולל settings (למשל live_stream_url, default_sound_id)

6) PUT /api/devices/{device_id}/status
   פרמ׳: status

7) DELETE /api/devices/{device_id}

8) DELETE /api/devices/user/{user_id}/delete-all
   פרמ׳: delete_notifications, delete_chat_messages, delete_push_subscriptions, confirm_deletion

9) DELETE /api/devices/user/{user_id}/delete-all-safe


Push Notifications – רישום, שליחה, ביטול, צפייה
1) POST /api/push/subscribe
   גוף: { user_id, endpoint, keys:{ p256dh, auth } }

2) DELETE /api/push/unsubscribe/{user_id}
   פרמ׳: endpoint? להסרה ממוקדת

3) GET /api/push/subscriptions/{user_id}

4) POST /api/push/send
   גוף:
   {
     user_id, device_id, title, body,
     icon?, badge?, image?,
     video_url?,          // חדש – וידאו לתצוגת "Latest Event Video"
     sound_id?, sound_url?, // צליל התראה (see /api/sounds/{id})
     data?, actions?, require_interaction?
   }
   הערות:
   - data.device_id חובה להעמקה לצ'אט של התקן
   - data.video_url (אם יש) יפתח צ'אט עם וידאו זה בראש
   - אם נשלח sound_id ללא sound_url – ה־SW ממפה ל־/api/sounds/{sound_id}

דוגמת curl מלאה:
```
curl -X POST "$BACKEND/api/push/send" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"demo-user-123",
    "device_id":"123456",
    "title":"Front Door Alert",
    "body":"Motion detected near the door",
    "image":"https://example.com/images/frame.jpg",
    "video_url":"https://example.com/videos/clip-123456.mp4",
    "sound_id":"significant",
    "data":{ "device_id":"123456", "video_url":"https://example.com/videos/clip-123456.mp4" },
    "require_interaction":true
  }'
```


התראות (Notifications)
1) GET /api/notifications/{user_id}
   פרמ׳: limit?, unread_only?

2) GET /api/notifications/{user_id}/device/{device_id}

3) PUT /api/notifications/{notification_id}/read

4) POST /api/simulate/device-notification
   פרמ׳: user_id, device_id, message, media_url?, notification_type?=message


צ׳אט (Chat)
1) POST /api/chat/send?user_id=...
   גוף: {
     device_id, message, sender='user',
     file_ids?, media_url?, media_urls?, referenced_messages?
   }
   התנהגות:
   - אם צורפו מדיה (file_ids/‏media_urls) – שימוש ב־Vision
   - פקודות בשפה טבעית לזיהוי: שינוי תפקיד/הוראות AI, עדכון Camera Prompt
   - לפעמים יוחזר אישור במקום תשובת AI (כאשר זוהה שינוי הגדרות)
   תשובה: { success, message_id, ai_response? }

2) GET /api/chat/{user_id}/{device_id}
   תשובה: רשימת הודעות (כרונולוגית)

3) GET /api/chat/{user_id}/{device_id}/history
   תשובה: { device_id, history:[...] } – היסטוריה מלאה בפורמט JSON

4) DELETE /api/chat/{user_id}/{device_id}/history

5) POST /api/chat/image-direct?user_id=...
   גוף: {
     device_id,
     image_data?,          // base64, ללא prefix
     image_url?,           // URL יחיד
     media_urls?,          // URL-ים מרובים
     video_url?,           // חדש – וידאו נלווה לתצוגה בראש הצ׳אט
     question?             // שאלה/הנחיה לניתוח
   }
   התנהגות:
   - המערכת מורידה תמונות מ־URL וממירה ל־base64 (timeout ~10s, בודק content-type)
   - AI מחליט אם להציג בצ׳אט (displayed_in_chat) ע"פ ה־Camera Prompt
   - אם displayed_in_chat=true:
     * נשמרת הודעת משתמש + תשובת AI בצ׳אט
     * אם video_url נשלח – נוצרת גם התראה עם media_url=video_url (ל"Latest Event Video")
     * נשלחת התראת Push (significant)
   תשובה: { success, displayed_in_chat, ai_response, message_id, analysis_type }

דוגמת curl (URL יחיד + וידאו):
```
curl -X POST "$BACKEND/api/chat/image-direct?user_id=demo-user-123" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id":"123456",
    "image_url":"https://example.com/frame.jpg",
    "video_url":"https://example.com/clip.mp4",
    "question":null
  }'
```


הגדרות AI (Chat Settings) – Role/Instructions + Natural Language Commands
1) GET /api/chat/settings/{user_id}/{device_id}
   תשובה: { role_name, system_message, instructions, model }

2) PUT /api/chat/settings/{user_id}/{device_id}
   גוף: { role_name?, system_message?, instructions?, model? }

3) POST /api/chat/settings/parse-command
   גוף: { user_id, device_id, message }
   תפקיד: לזהות פקודות טבעיות לשינוי Role/Instructions ולהחיל אותן. מחזיר אישור.


פרומפט מצלמה (Camera Prompt)
1) GET /api/camera/prompt/{user_id}/{device_id}
   תשובה: { success, prompt_text, instructions }

2) PUT /api/camera/prompt/{user_id}/{device_id}
   גוף: { instructions }
   התנהגות: בונה Prompt מלא ע"פ ההנחיות ושומר.

3) POST /api/camera/prompt/parse-command
   גוף: { user_id, device_id, message }
   תפקיד: לזהות אינטנט טבעי ("monitor for...", "look for...") ולעדכן. יוצר הודעת system בצ׳אט.

4) POST /api/camera/prompt/fix-from-feedback
   גוף: { user_id, device_id, message, referenced_messages? }
   תפקיד: כאשר מצהירים שהניתוח היה שגוי – מייצר Prompt משופר, שומר, ויוצר הודעת system מאשרת.


קבצים (Files)
1) POST /api/files/upload (multipart/form-data)
   שדות: file, user_id, device_id?, message_id?
   תשובה: { success, file_id, url, ... }

2) GET /api/files/{file_id}

3) GET /api/files/user/{user_id}

4) DELETE /api/files/{file_id}


סימולציה
1) POST /api/simulate/device-notification
   פרמ׳: user_id, device_id, message, media_url?, notification_type?=message


סטטוס ובריאות
- GET /api/
- GET /api/status
- POST /api/status


דיווחי Push בצד ה־Frontend (Service Worker)
- בעת קבלת push, אם data.device_id קיים – פתיחה/מיקוד ל־/?device_id=...
- אם data.video_url קיים – העברת video_url לעמוד, כדי להציג כ־Latest Event Video ספציפי
- צלילים: אם נשלח sound_id ללא sound_url – ה־SW ממפה ל־/api/sounds/{sound_id}; בנוסף, יש הודעת postMessage לפלייבק גם מהעמוד עצמו (Compatibility)


שגיאות נפוצות
- Missing fields: מחזיר success:false + error
- URL invalid/non-image: מחזיר success:false + error עבור image-direct
- Token/JWT חסר או לא תקין: auth/me יחזיר authenticated:false
- WebSocket: ניתוקים – הקליינט מנסה להתחבר מחדש ומציג הודעת מצב


דגשים תפעוליים
- user_id הוא אימייל המשתמש המחובר (JWT) כאשר עובדים במצב עם Auth. בתצורה הנוכחית (Rollout) יש fallback ל־demo-user-123 ב־Frontend הישן.
- לכל ראוט Backend – השתמשו ב־{REACT_APP_BACKEND_URL}/api ... בלבד.
- לניתוח תמונה ישיר – עדיף לשלוח image_url/‏media_urls (HTTP/HTTPS, content-type ״image/*"). לבסיס64 – להשמיט את ה־prefix.
- התראות push: מומלץ לכלול data.device_id ותמיד להעביר video_url אם רוצים שהצ׳אט יפתח עם הווידאו הזה.


נספח – דוגמאות נוספות
1) שליחת הודעת צ׳אט עם קובץ ותמונת URL:
```
# העלאת קובץ
FID=$(curl -s -X POST "$BACKEND/api/files/upload" \
  -F "file=@/path/to/file.jpg" \
  -F "user_id=demo-user-123" -F "device_id=123456" | jq -r .file_id)

# שליחת הודעה
curl -X POST "$BACKEND/api/chat/send?user_id=demo-user-123" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\":\"123456\",\"message\":\"Check this\",\"file_ids\":[\"$FID\"],\"media_urls\":[\"https://example.com/image.jpg\"]}"
```

2) הצגת היסטוריית צ׳אט מלאה:
```
curl "$BACKEND/api/chat/demo-user-123/123456/history"
```

3) תיקון פרומפט מצלמה על בסיס משוב:
```
curl -X POST "$BACKEND/api/camera/prompt/fix-from-feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"demo-user-123",
    "device_id":"123456",
    "message":"הניתוח היה שגוי – זה היה צל ולא אדם. התמקדו בתנועה רציפה של אדם ליד הידית והתעלמו מצללים.",
    "referenced_messages":[]
  }'
```

4) שליחת Push עם צליל מובנה:
```
curl -X POST "$BACKEND/api/push/send" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"demo-user-123",
    "device_id":"123456",
    "title":"Significant Activity",
    "body":"Person at the door",
    "sound_id":"significant",
    "data":{"device_id":"123456"}
  }'
```

—
מסמך זה מכסה את כלל ה־Endpoints, ההתנהגויות והדגשים במערכת MAI Focus. במידה ותרצה שנייצא את המסמך ל־OpenAPI 3.1 (Swagger) עבור אינטגרציות נוספות – עדכן ואייצר קובץ spec מלא לתשתית שלך.
