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

// Dynamically use current hostname (works for Docker + dev)
const hostname = window.location.hostname;
const WS_BASE_URL = `ws://${hostname}:8000`;

console.log('🔍 WebSocket configuration:', {
  hostname: hostname,
  baseUrl: WS_BASE_URL,
  currentLocation: window.location.href,
  isDocker: hostname !== 'localhost' && hostname !== '127.0.0.1'
});

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
      
      const wsUrl = `${WS_BASE_URL}/api/ws/${promptId}`;
      
      console.log('🔌 Attempting WebSocket connection...');
      console.log('🔌 WebSocket URL:', wsUrl);
      console.log('🔌 Prompt ID:', promptId);
      console.log('🔌 Current WebSocket state:', this.ws?.readyState);

      try {
        this.ws = new WebSocket(wsUrl);
        console.log('🔌 WebSocket object created, readyState:', this.ws.readyState);

        this.ws.onopen = (event) => {
          console.log(`✅ WebSocket OPENED successfully for prompt ${promptId}`);
          console.log('🔌 Open event details:', event);
          console.log('🔌 WebSocket readyState after open:', this.ws?.readyState);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            console.log('📨 WebSocket message received:', event.data);
            const message: WebSocketMessage = JSON.parse(event.data);
            console.log('📨 Parsed message:', message);
            this.notifyListeners(message);
          } catch (error) {
            console.error('❌ Failed to parse WebSocket message:', error, event.data);
          }
        };

        this.ws.onclose = (event) => {
          console.log('🚪 WebSocket connection CLOSED');
          console.log('🚪 Close code:', event.code);
          console.log('🚪 Close reason:', event.reason);
          console.log('🚪 Was clean close:', event.wasClean);
          console.log('🚪 Close event details:', event);
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket ERROR occurred:');
          console.error('❌ Error details:', error);
          console.error('❌ WebSocket readyState during error:', this.ws?.readyState);
          console.error('❌ WebSocket URL during error:', wsUrl);
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
