import type { WSMessage } from "./schema";

type Handler = (message: WSMessage) => void;

type EchoWebSocketOptions = {
  maxReconnectAttempts?: number;
  reconnectDelayMs?: number;
  onOpen?: () => void;
  onClose?: () => void;
  onMessage?: Handler;
  onError?: (error: Event) => void;
};

export class EchoWebSocket {
  private readonly url: string;
  private readonly options: Required<EchoWebSocketOptions>;
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private closedByUser = false;
  private queue: string[] = [];
  private heartbeatTimer: number | null = null;

  constructor(url: string, options?: EchoWebSocketOptions) {
    this.url = url;
    this.options = {
      maxReconnectAttempts: options?.maxReconnectAttempts ?? 8,
      reconnectDelayMs: options?.reconnectDelayMs ?? 800,
      onOpen: options?.onOpen ?? (() => undefined),
      onClose: options?.onClose ?? (() => undefined),
      onMessage: options?.onMessage ?? (() => undefined),
      onError: options?.onError ?? (() => undefined)
    };
  }

  connect(): void {
    this.closedByUser = false;
    this.socket = new WebSocket(this.url);

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.flushQueue();
      this.startHeartbeat();
      this.options.onOpen();
    };

    this.socket.onclose = () => {
      this.stopHeartbeat();
      this.options.onClose();
      if (!this.closedByUser && this.reconnectAttempts < this.options.maxReconnectAttempts) {
        this.reconnectAttempts += 1;
        window.setTimeout(() => this.connect(), this.options.reconnectDelayMs * this.reconnectAttempts);
      }
    };

    this.socket.onerror = (event) => {
      this.options.onError(event);
    };

    this.socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as WSMessage;
        this.options.onMessage(payload);
      } catch {
        this.options.onMessage({ type: "error", message: "Malformed websocket payload." });
      }
    };
  }

  disconnect(): void {
    this.closedByUser = true;
    this.stopHeartbeat();
    this.socket?.close();
    this.socket = null;
  }

  send(payload: WSMessage): void {
    const encoded = JSON.stringify(payload);
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(encoded);
      return;
    }
    this.queue.push(encoded);
  }

  private flushQueue(): void {
    while (this.queue.length > 0 && this.socket?.readyState === WebSocket.OPEN) {
      const message = this.queue.shift();
      if (message) {
        this.socket.send(message);
      }
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = window.setInterval(() => {
      this.send({ type: "ping" });
    }, 10_000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      window.clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}
