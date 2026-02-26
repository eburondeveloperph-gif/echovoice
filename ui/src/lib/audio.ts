export async function blobToBase64(blob: Blob): Promise<string> {
  const buffer = await blob.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

export function base64ToUint8Array(value: string): Uint8Array {
  const binary = atob(value);
  const output = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    output[i] = binary.charCodeAt(i);
  }
  return output;
}

export async function listAudioInputDevices(): Promise<MediaDeviceInfo[]> {
  if (!navigator.mediaDevices?.enumerateDevices) {
    return [];
  }
  const devices = await navigator.mediaDevices.enumerateDevices();
  return devices.filter((device) => device.kind === "audioinput");
}

export class MicCapture {
  private stream: MediaStream | null = null;
  private recorder: MediaRecorder | null = null;
  private analyser: AnalyserNode | null = null;
  private audioContext: AudioContext | null = null;
  private levelRafId: number | null = null;
  private isRecording = false;

  async start(options: {
    deviceId?: string;
    onChunk: (base64Chunk: string) => void;
    onLevel?: (level: number) => void;
  }): Promise<void> {
    if (this.isRecording) {
      return;
    }

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: options.deviceId
        ? {
            deviceId: { exact: options.deviceId },
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        : {
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
    });

    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";

    this.recorder = new MediaRecorder(this.stream, { mimeType });
    this.recorder.ondataavailable = async (event: BlobEvent) => {
      if (event.data.size === 0) {
        return;
      }
      const encoded = await blobToBase64(event.data);
      options.onChunk(encoded);
    };

    this.audioContext = new AudioContext();
    const source = this.audioContext.createMediaStreamSource(this.stream);
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 2048;
    source.connect(this.analyser);

    if (options.onLevel) {
      this.pushAudioLevels(options.onLevel);
    }

    this.recorder.start(250);
    this.isRecording = true;
  }

  stop(): void {
    if (!this.isRecording) {
      return;
    }

    this.recorder?.stop();
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;

    if (this.levelRafId !== null) {
      cancelAnimationFrame(this.levelRafId);
      this.levelRafId = null;
    }

    this.audioContext?.close();
    this.audioContext = null;
    this.recorder = null;
    this.analyser = null;
    this.isRecording = false;
  }

  active(): boolean {
    return this.isRecording;
  }

  private pushAudioLevels(onLevel: (level: number) => void): void {
    if (!this.analyser) {
      return;
    }

    const data = new Uint8Array(this.analyser.frequencyBinCount);
    const tick = () => {
      if (!this.analyser) {
        return;
      }
      this.analyser.getByteTimeDomainData(data);
      let sum = 0;
      for (let i = 0; i < data.length; i += 1) {
        const normalized = (data[i] - 128) / 128;
        sum += normalized * normalized;
      }
      const rms = Math.sqrt(sum / data.length);
      onLevel(Math.min(1, rms * 3));
      this.levelRafId = requestAnimationFrame(tick);
    };
    this.levelRafId = requestAnimationFrame(tick);
  }
}
