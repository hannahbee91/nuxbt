class WebRTCManager {
  private pc: RTCPeerConnection | null = null;
  private dc: RTCDataChannel | null = null;
  private handlers: Record<string, ((data: any) => void)[]> = {};
  private pendingEmits: { type: string; data: any; id?: string }[] = [];
  private responseCallbacks: Record<string, (resp: any) => void> = {};
  private nextId = 0;
  public connected = false;

  constructor() {
    this.connect();
  }

  private async connect() {
    if (this.pc) {
      this.pc.close();
    }

    this.pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    });

    // We must create the data channel before the offer
    this.dc = this.pc.createDataChannel('nuxbt');
    this.setupDataChannel(this.dc);

    const offer = await this.pc.createOffer();
    await this.pc.setLocalDescription(offer);

    try {
      const response = await fetch('/offer', {
        method: 'POST',
        body: JSON.stringify({
          sdp: this.pc.localDescription!.sdp,
          type: this.pc.localDescription!.type,
        }),
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) throw new Error('Signaling failed');

      const answer = await response.json();
      await this.pc.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (err) {
      console.error('WebRTC connection error:', err);
      setTimeout(() => this.connect(), 5000);
    }
  }

  private setupDataChannel(dc: RTCDataChannel) {
    dc.onopen = () => {
      console.log('WebRTC DataChannel opened');
      this.connected = true;
      this.emitPending();
      this.trigger('connect', null);
    };
    dc.onclose = () => {
      console.log('WebRTC DataChannel closed');
      this.connected = false;
      this.trigger('disconnect', null);
      setTimeout(() => this.connect(), 5000);
    };
    dc.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'response' && msg.id !== undefined) {
          this.responseCallbacks[msg.id]?.(msg.data);
          delete this.responseCallbacks[msg.id];
        } else {
          this.trigger(msg.type, msg.data);
        }
      } catch (err) {
        console.error('Error parsing DataChannel message:', err);
      }
    };
    dc.onerror = (e) => {
      console.error('DataChannel error:', e);
    };
  }

  private trigger(type: string, data: any) {
    this.handlers[type]?.forEach((h) => h(data));
  }

  public on(type: string, handler: (data: any) => void) {
    if (!this.handlers[type]) this.handlers[type] = [];
    this.handlers[type].push(handler);
  }

  public off(type: string, handler: (data: any) => void) {
    if (!this.handlers[type]) return;
    this.handlers[type] = this.handlers[type].filter((h) => h !== handler);
  }

  public emit(type: string, data?: any, callback?: (resp: any) => void) {
    const id = callback ? (this.nextId++).toString() : undefined;
    if (id && callback) this.responseCallbacks[id] = callback;

    const payload = { type, data, id };
    if (this.dc?.readyState === 'open') {
      this.dc.send(JSON.stringify(payload));
    } else {
      this.pendingEmits.push({ type, data, id });
    }
  }

  private emitPending() {
    while (this.pendingEmits.length > 0) {
      const payload = this.pendingEmits.shift()!;
      this.dc?.send(JSON.stringify(payload));
    }
  }
}

export const socket = new WebRTCManager();
