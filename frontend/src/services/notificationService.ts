// C:\Users\Vinay\Project\frontend\src\services\notificationService.ts

// The problematic top-level import has been removed.
// import { useNotificationStore } from '@/stores/notification';

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
    console.log("Service: isConnecting lock set to TRUE.");

    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
      console.error("Service: No auth token found. Aborting.");
      this.isConnecting = false;
      return;
    }

    const url = `ws://localhost:8000/ws/notifications/?token=${authToken}`;
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log("✅ Service: WebSocket connection established successfully.");
      this.isConnecting = false; // Release the lock
    };

    // --- FIX APPLIED HERE ---
    // The onmessage handler is now an async function.
    // The store is imported dynamically only when a message is received, breaking the circular dependency.
    this.socket.onmessage = async (event) => {
      try {
        // Dynamically import the store *inside* the function that needs it.
        const { useNotificationStore } = await import('@/stores/notification');
        const store = useNotificationStore();
        
        const data = JSON.parse(event.data);
        if (data.type === 'notification' && data.message) {
          store.addLiveNotification(data.message.payload);
        }
      } catch (e) {
          console.error("Service: Error processing message or importing store:", e);
      }
    };
    // --- END OF FIX ---

    this.socket.onclose = () => {
      console.log("Service: WebSocket connection closed.");
      this.socket = null;
      this.isConnecting = false; // Release the lock
    };

    this.socket.onerror = (error) => {
      console.error("Service: WebSocket error:", error);
      this.isConnecting = false; // Release the lock
    };
  }

  public disconnect(): void {
    if (this.socket) {
      console.log("Service: disconnect() called, closing socket.");
      this.socket.close();
    }
  }
}

// The singleton instance is exported as before.
export const notificationService = new NotificationService();