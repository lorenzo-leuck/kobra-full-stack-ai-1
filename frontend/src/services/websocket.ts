interface StatusUpdate {
  type: 'status_update';
  data: {
    prompt_id: string;
    overall_status: string;
    current_step: number;
    total_steps: number;
    progress: number;
    messages: string[];
  };
}

interface SessionUpdate {
  type: 'session_update';
  data: {
    prompt_id: string;
    session_id: string;
    stage: string;
    status: string;
    logs: string[];
  };
}

type WebSocketMessage = StatusUpdate | SessionUpdate;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private promptId: string | null = null;
  private listeners: Set<(message: WebSocketMessage) => void> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(promptId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.promptId = promptId;
      
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
      const wsUrl = apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://').replace('/api', '') + `/api/ws/${promptId}`;

      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log(`WebSocket connected for prompt ${promptId}`);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.notifyListeners(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket connection closed:', event.code, event.reason);
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.promptId) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect(this.promptId!).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  addListener(callback: (message: WebSocketMessage) => void) {
    this.listeners.add(callback);
  }

  removeListener(callback: (message: WebSocketMessage) => void) {
    this.listeners.delete(callback);
  }

  private notifyListeners(message: WebSocketMessage) {
    this.listeners.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in WebSocket listener:', error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.promptId = null;
    this.listeners.clear();
    this.reconnectAttempts = 0;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const websocketService = new WebSocketService();
