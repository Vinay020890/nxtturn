// C:\Users\Vinay\Project\frontend\src\services\notificationService.ts
// --- UPGRADED VERSION ---

class NotificationService {
  private socket: WebSocket | null = null;
  private isConnecting: boolean = false;

  public connect(): void {
    console.log("Service: connect() called.");

    if (this.isConnecting || (this.socket && this.socket.readyState === WebSocket.OPEN)) {
      console.log("Service: Connection attempt ignored, already connecting or connected.");
      return;
    }

    this.isConnecting = true;
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
      console.error("Service: No auth token found. Aborting.");
      this.isConnecting = false;
      return;
    }
    
    // --- CHANGE 1: Update the WebSocket endpoint URL ---
    const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws/';
    const url = `${baseUrl}activity/?token=${authToken}`; // Use the new 'activity' path
    console.log(`Service: Attempting to connect to WebSocket at: ${url}`);

    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log("✅ Service: WebSocket connection established successfully.");
      this.isConnecting = false;
    };

    // --- CHANGE 2: Create a powerful message handler that dispatches to multiple stores ---
    this.socket.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        const eventType = data.type;
        const message = data.message;

        if (!eventType || !message) {
            console.warn("Service: Received malformed message", data);
            return;
        }

        console.log(`Service: Received event type: '${eventType}'`, message);
        
        switch (eventType) {
          case 'notification': {
            const { useNotificationStore } = await import('@/stores/notification');
            const store = useNotificationStore();
            store.addLiveNotification(message.payload);
            break;
          }
          case 'live_post': {
            const { useFeedStore } = await import('@/stores/feed');
            const store = useFeedStore();
            store.addNewPostFromLiveUpdate(message.payload);
            break;
          }
          default:
            console.warn(`Service: Unhandled event type: '${eventType}'`);
        }
      } catch (e) {
          console.error("Service: Error processing message or importing store:", e);
      }
    };

    this.socket.onclose = () => {
      console.log("Service: WebSocket connection closed.");
      this.socket = null;
      this.isConnecting = false;
    };

    this.socket.onerror = (error) => {
      console.error("Service: WebSocket error:", error);
      this.isConnecting = false;
    };
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.close();
    }
  }
}

export const notificationService = new NotificationService();