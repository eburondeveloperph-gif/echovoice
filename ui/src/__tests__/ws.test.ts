import { vi } from "vitest";

import { EchoWebSocket } from "../lib/ws";

class MockWebSocket {
  static OPEN = 1;
  static instances: MockWebSocket[] = [];
  readyState = 1;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor() {
    MockWebSocket.instances.push(this);
    setTimeout(() => this.onopen?.(), 0);
  }

  send() {
    return undefined;
  }

  close() {
    this.onclose?.();
  }
}

describe("EchoWebSocket", () => {
  it("reconnects after unexpected close", async () => {
    vi.useFakeTimers();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (globalThis as any).WebSocket = MockWebSocket;

    const onOpen = vi.fn();
    const socket = new EchoWebSocket("ws://localhost/ws", {
      onOpen,
      reconnectDelayMs: 5
    });

    socket.connect();
    await vi.runOnlyPendingTimersAsync();

    expect(onOpen).toHaveBeenCalledTimes(1);

    MockWebSocket.instances[0]?.close();
    await vi.advanceTimersByTimeAsync(20);

    expect(onOpen).toHaveBeenCalledTimes(2);
    socket.disconnect();
  });
});
