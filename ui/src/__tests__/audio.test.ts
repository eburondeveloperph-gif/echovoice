import { MicCapture } from "../lib/audio";

class FakeMediaRecorder {
  static isTypeSupported() {
    return true;
  }

  ondataavailable: ((event: BlobEvent) => void) | null = null;

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  constructor(_stream: MediaStream, _options?: { mimeType?: string }) {}

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  start(_sliceMs?: number) {
    return undefined;
  }

  stop() {
    return undefined;
  }
}

class FakeAudioContext {
  createMediaStreamSource() {
    return { connect: () => undefined };
  }

  createAnalyser() {
    return {
      fftSize: 2048,
      frequencyBinCount: 32,
      getByteTimeDomainData: (arr: Uint8Array) => arr.fill(128)
    };
  }

  close() {
    return Promise.resolve();
  }
}

describe("MicCapture", () => {
  it("starts and stops capture", async () => {
    const stream = {
      getTracks: () => [{ stop: () => undefined }]
    } as unknown as MediaStream;

    Object.defineProperty(globalThis, "MediaRecorder", { value: FakeMediaRecorder });
    Object.defineProperty(globalThis, "AudioContext", { value: FakeAudioContext });
    Object.defineProperty(globalThis.navigator, "mediaDevices", {
      value: {
        getUserMedia: async () => stream
      },
      configurable: true
    });

    const capture = new MicCapture();
    await capture.start({ onChunk: () => undefined });
    expect(capture.active()).toBe(true);
    capture.stop();
    expect(capture.active()).toBe(false);
  });
});
