// C:\Users\Vinay\Project\frontend\src\services\notificationService.ts

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
    
    // --- THIS IS THE FIX ---
    // The hardcoded 'localhost' is replaced with the environment variable.
    const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws/';
    const url = `${baseUrl}notifications/?token=${authToken}`;
    console.log(`Service: Attempting to connect to WebSocket at: ${url}`); // Added for easier debugging
    // --- END OF FIX ---

    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log("✅ Service: WebSocket connection established successfully.");
      this.isConnecting = false;
    };

    this.socket.onmessage = async (event) => {
      try {
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
      console.log("Service: disconnect() called, closing socket.");
      this.socket.close();
    }
  }
}

export const notificationService = new NotificationService();