// C:\Users\Vinay\Project\frontend\src\services\notificationService.ts
// --- FIX for TypeScript null error ---

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
    
    const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws/';
    const url = `${baseUrl}activity/?token=${authToken}`;
    console.log(`Service: Attempting to connect to WebSocket at: ${url}`);

    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log("✅ Service: WebSocket connection established successfully.");
      this.isConnecting = false;
    };

    this.socket.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        
        const eventType = data.type;
        const payload = data.payload || data;
        
        if (!eventType) {
            console.warn("Service: Received malformed message, missing 'type'", data);
            return;
        }

        console.log(`Service: Received event type: '${eventType}'`, payload);
        
        switch (eventType) {
          case 'new_notification': {
            const { useNotificationStore } = await import('@/stores/notification');
            const store = useNotificationStore();
            store.addLiveNotification(payload);
            break;
          }
          case 'new_post': {
            const { useFeedStore } = await import('@/stores/feed');
            const store = useFeedStore();
            store.handleNewPostSignal(payload.id);
            break;
          }
          case 'post_deleted': {
            const postId = payload.post_id;
            if (!postId) {
              console.warn("Service: Received post_deleted event but missing post_id", payload);
              return;
            }

            console.log(`🚀 Service: Dispatching delete for post ID ${postId} to all stores.`);

            const { usePostsStore } = await import('@/stores/posts');
            const { useFeedStore } = await import('@/stores/feed');
            const { useProfileStore } = await import('@/stores/profile');
            const { useGroupStore } = await import('@/stores/group');

            const postsStore = usePostsStore();
            const feedStore = useFeedStore();
            const profileStore = useProfileStore();
            const groupStore = useGroupStore();

            postsStore.removePost(postId);
            feedStore.handlePostDeletedSignal(postId);
            profileStore.handlePostDeletedSignal(postId);
            groupStore.handlePostDeletedSignal(postId);
            break;
          }
          default:
            // This handles the older message format gracefully
            if (data.type === 'send_notification' || data.type === 'send_live_post') {
                console.log(`Service: Handling legacy message format for ${data.type}`);
                
                // [TYPESCRIPT FIX] Add a null check before calling onmessage
                if (this.socket && this.socket.onmessage) {
                  this.socket.onmessage(new MessageEvent('message', {data: JSON.stringify(data.message)}));
                }

            } else {
                console.warn(`Service: Unhandled event type: '${eventType}'`);
            }
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