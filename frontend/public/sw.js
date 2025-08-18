// Service Worker for Device Chat PWA
/* global self, caches, clients */

const CACHE_NAME = 'device-chat-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.log('Service Worker install failed:', error);
      })
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  event.respondWith(  
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});

// Activate event
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Push notification handling
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event);
  
  let notificationData = {
    title: 'Device Chat',
    body: 'New notification from your device',
    icon: '/manifest-icon-192.png',
    badge: '/manifest-icon-192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/manifest-icon-192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/manifest-icon-192.png'
      }
    ]
  };

  // Parse notification data if available
  if (event.data) {
    try {
      const payload = event.data.json();
      notificationData = {
        ...notificationData,
        ...payload,
        data: { ...(notificationData.data || {}), ...(payload.data || {}) }
      };
    } catch (e) {
      console.error('Error parsing push notification data:', e);
      notificationData.body = event.data.text() || notificationData.body;
    }
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      image: notificationData.image,
      vibrate: notificationData.vibrate,
      data: notificationData.data,
      actions: notificationData.actions,
      requireInteraction: notificationData.requireInteraction || false,
      tag: 'device-chat-notification'
    })
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  event.notification.close();

  if (event.action === 'view' || !event.action) {
    const data = event.notification && event.notification.data ? event.notification.data : {};
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // If app is already open, focus it
        for (const client of clientList) {
          if (client.url.startsWith(self.location.origin) && 'focus' in client) {
            client.postMessage({ type: 'navigate_to_device', device_id: data.device_id, video_url: data.video_url });
            return client.focus();
          }
        }
        // Otherwise, open new window
        if (clients.openWindow) {
          // Deep-link into the device chat if device_id is present in data
          if (data && data.device_id) {
            const qs = new URLSearchParams({ device_id: data.device_id, video_url: data.video_url || '' }).toString();
            const target = `/?${qs}`;
            return clients.openWindow(target);
          }
          return clients.openWindow('/');
        }
      })
    );
  }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'device-chat-sync') {
    event.waitUntil(
      // Sync offline actions when connection is restored
      syncOfflineActions()
    );
  }
});

async function syncOfflineActions() {
  // Implement offline action syncing if needed
  console.log('Syncing offline actions...');
}