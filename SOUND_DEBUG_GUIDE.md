# Notification Sound Debug Guide

## Issue: Notification sounds not playing

## Quick Debugging Steps

### Step 1: Check Browser Console
1. Open the app in your browser
2. Press `F12` to open Developer Tools
3. Go to the **Console** tab
4. Look for any errors or warnings related to sound/audio

### Step 2: Test Sound Directly in Browser
Open browser console (F12) and run:

```javascript
// Test if sound API is accessible
const audio = new Audio('https://aidevicechat.preview.emergentagent.com/api/sounds/alert');
audio.play().then(() => {
  console.log('✅ Sound played successfully!');
}).catch((error) => {
  console.error('❌ Sound failed to play:', error);
});
```

### Step 3: Check Service Worker Status
In browser console:

```javascript
// Check if service worker is active
navigator.serviceWorker.ready.then(registration => {
  console.log('✅ Service Worker is ready:', registration);
}).catch(error => {
  console.error('❌ Service Worker error:', error);
});
```

### Step 4: Check Push Subscription
In browser console:

```javascript
// Check if push is subscribed
navigator.serviceWorker.ready.then(async (registration) => {
  const subscription = await registration.pushManager.getSubscription();
  if (subscription) {
    console.log('✅ Push subscription active:', subscription.endpoint);
  } else {
    console.log('❌ No push subscription found');
  }
});
```

### Step 5: Test Sound Message from Service Worker
In browser console:

```javascript
// Manually trigger sound playback
navigator.serviceWorker.ready.then(registration => {
  // Simulate SW posting a sound message
  navigator.serviceWorker.controller.postMessage({
    type: 'play_sound',
    sound_id: 'alert',
    sound_url: 'https://aidevicechat.preview.emergentagent.com/api/sounds/alert'
  });
  console.log('✅ Sent play_sound message to page');
});
```

---

## Common Issues & Solutions

### Issue 1: Browser Autoplay Policy
**Problem:** Browsers block audio until user interaction.

**Solution:** 
1. Click anywhere on the page first
2. Then send the notification

**Test in console:**
```javascript
// This should work after clicking on page
document.body.addEventListener('click', () => {
  const audio = new Audio('https://aidevicechat.preview.emergentagent.com/api/sounds/alert');
  audio.play();
}, { once: true });
console.log('Click anywhere on the page to test sound...');
```

---

### Issue 2: App Not Open When Notification Arrives
**Problem:** Sounds only play when the app is open in a browser tab.

**Solution:** Keep the app open in at least one browser tab.

---

### Issue 3: Service Worker Not Registered
**Problem:** Service worker not active.

**Solution:** Check in DevTools → Application → Service Workers
- Should see "Activated and running"
- If not, try unregistering and reloading:

```javascript
// Unregister service worker
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(r => r.unregister());
  console.log('Service workers unregistered. Reload page.');
});
```

---

### Issue 4: Sound File Not Loading (CORS/404)
**Problem:** Sound URL returns error.

**Test sound URL directly:**
```bash
curl -I https://aidevicechat.preview.emergentagent.com/api/sounds/alert
```

Should return: `HTTP/2 200` and `Content-Type: audio/wav`

---

## Manual Sound Test Commands

### Test 1: Play Sound Directly in App (Browser Console)
```javascript
const audio = new Audio('https://aidevicechat.preview.emergentagent.com/api/sounds/alert');
audio.volume = 1.0;
audio.play().then(() => {
  console.log('✅ Alert sound played');
}).catch(err => {
  console.error('❌ Failed:', err.message);
});
```

### Test 2: Test All Sounds
```javascript
const sounds = ['alert', 'significant', 'routine'];
let index = 0;

function playNext() {
  if (index < sounds.length) {
    const soundId = sounds[index];
    console.log(`🔊 Playing: ${soundId}`);
    const audio = new Audio(`https://aidevicechat.preview.emergentagent.com/api/sounds/${soundId}`);
    audio.play().then(() => {
      console.log(`✅ ${soundId} played successfully`);
      index++;
      setTimeout(playNext, 2000); // Wait 2 seconds between sounds
    }).catch(err => {
      console.error(`❌ ${soundId} failed:`, err.message);
      index++;
      playNext();
    });
  } else {
    console.log('🎵 All sounds tested');
  }
}

// Start after user clicks page
document.body.addEventListener('click', () => {
  playNext();
}, { once: true });
console.log('👆 Click anywhere on page to test all sounds...');
```

---

## Send Notification with Sound (via curl)

### Working Command:
```bash
curl --location 'https://aidevicechat.preview.emergentagent.com/api/push/send' \
--header 'Content-Type: application/json' \
--data '{
    "user_id": "menibl1111@gmail.com",
    "device_id": "123456",
    "title": "🔔 Sound Test",
    "body": "Testing notification sound",
    "sound_id": "alert",
    "require_interaction": false
}'
```

**Important:** The app MUST be open in your browser for sound to play!

---

## Checklist

Before sending notification, ensure:

- [ ] App is open in browser
- [ ] You are logged in as `menibl1111@gmail.com`
- [ ] Camera `123456` exists for this user
- [ ] Notification permission is granted
- [ ] Push subscription is active (bell icon in header)
- [ ] You have clicked on the page (for autoplay permission)
- [ ] Browser console shows no errors
- [ ] Service worker is active

---

## Expected Behavior

1. **Notification arrives** → You see browser notification popup
2. **Service Worker** → Posts `play_sound` message to page
3. **App (if open)** → Receives message and plays sound
4. **Sound plays** → You hear the alert/significant/routine tone

---

## If Still Not Working

### Debug Output Command
Run this in browser console while app is open:

```javascript
// Enable debug logging
localStorage.setItem('debug_sounds', 'true');

// Listen for all service worker messages
navigator.serviceWorker.addEventListener('message', (event) => {
  console.log('📬 SW Message received:', event.data);
  if (event.data.type === 'play_sound') {
    console.log('🔊 SOUND MESSAGE:', {
      sound_id: event.data.sound_id,
      sound_url: event.data.sound_url
    });
  }
});

console.log('✅ Debug logging enabled. Send a notification now.');
```

Then send a notification and check what appears in console.

---

## Advanced: Force Sound Play on Notification

If you want to guarantee sound plays, you can test by opening browser console and pasting:

```javascript
// Subscribe to all notifications and force play sound
navigator.serviceWorker.ready.then(registration => {
  registration.addEventListener('message', (event) => {
    if (event.data.type === 'play_sound') {
      const url = event.data.sound_url || 
                  `https://aidevicechat.preview.emergentagent.com/api/sounds/${event.data.sound_id}`;
      
      console.log('🔊 Attempting to play:', url);
      
      const audio = new Audio(url);
      audio.volume = 1.0;
      audio.play()
        .then(() => console.log('✅ Sound played successfully!'))
        .catch(err => console.error('❌ Sound failed:', err));
    }
  });
  console.log('✅ Listening for sound messages');
});
```

---

## Contact Support

If none of these steps work, please provide:
1. Browser name and version
2. Console errors (screenshot)
3. Service Worker status (screenshot from DevTools → Application → Service Workers)
4. Result of sound test commands above
