import { API_BASE_URL } from "./config";
import type { MotorEreignis } from "../types/motor";

const WS_URL = `${API_BASE_URL.replace(/^http/, "ws")}/motor/ws`;
const RECONNECT_VERZOEGERUNG_MS = 2000;

/** Hält die WebSocket-Verbindung zum Motor, reconnected bei Abbruch. */
export class MotorVerbindung {
  private socket: WebSocket;
  private absichtlichGeschlossen = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private readonly aufEreignis: (e: MotorEreignis) => void,
    private readonly aufStatus?: (verbunden: boolean) => void,
  ) {
    this.socket = this.verbinden();
  }

  private verbinden(): WebSocket {
    const socket = new WebSocket(WS_URL);
    socket.onopen = () => this.aufStatus?.(true);
    socket.onmessage = (ev: MessageEvent) => {
      this.aufEreignis(JSON.parse(ev.data as string) as MotorEreignis);
    };
    socket.onerror = () => this.aufStatus?.(false);
    socket.onclose = () => {
      this.aufStatus?.(false);
      if (!this.absichtlichGeschlossen) {
        this.reconnectTimer = setTimeout(() => {
          this.socket = this.verbinden();
        }, RECONNECT_VERZOEGERUNG_MS);
      }
    };
    return socket;
  }

  private sendeJson(nachricht: unknown): void {
    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(nachricht));
    }
  }

  senden(text: string): void {
    this.sendeJson({ typ: "nutzer", text });
  }

  rueckfrageAntworten(id: string, erlaubt: boolean, antwort?: string): void {
    this.sendeJson({ typ: "rueckfrage_antwort", id, erlaubt, antwort: antwort ?? null });
  }

  abbrechen(): void {
    this.sendeJson({ typ: "abbrechen" });
  }

  neustart(): void {
    this.sendeJson({ typ: "neustart" });
  }

  schliessen(): void {
    this.absichtlichGeschlossen = true;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket.close();
  }
}
