import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MotorVerbindung } from "./motor";

// Gestubbtes globales WebSocket: eine Klasse mit static instances,
// send-Spy und manuell feuerbaren onopen/onmessage/onclose-Handlern.
class WebSocketStub {
  static readonly OPEN = 1;
  static instances: WebSocketStub[] = [];

  readyState = WebSocketStub.OPEN;
  send = vi.fn();
  close = vi.fn();
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public url: string) {
    WebSocketStub.instances.push(this);
  }
}

beforeEach(() => {
  WebSocketStub.instances = [];
  vi.stubGlobal("WebSocket", WebSocketStub);
});

afterEach(() => vi.unstubAllGlobals());

describe("api/motor", () => {
  it("verbindet auf der aus API_BASE_URL abgeleiteten ws-URL", () => {
    new MotorVerbindung(() => {});

    expect(WebSocketStub.instances).toHaveLength(1);
    expect(WebSocketStub.instances[0].url).toBe("ws://127.0.0.1:8000/motor/ws");
  });

  it("senden schreibt das Nutzer-Ereignis als JSON", () => {
    const verbindung = new MotorVerbindung(() => {});
    verbindung.senden("Hallo");

    const socket = WebSocketStub.instances[0];
    expect(socket.send).toHaveBeenCalledWith(JSON.stringify({ typ: "nutzer", text: "Hallo" }));
  });

  it("eingehende Nachrichten landen geparst beim Callback", () => {
    const aufEreignis = vi.fn();
    new MotorVerbindung(aufEreignis);
    const socket = WebSocketStub.instances[0];

    socket.onmessage?.({ data: JSON.stringify({ typ: "text_haeppchen", text: "Hi" }) });

    expect(aufEreignis).toHaveBeenCalledWith({ typ: "text_haeppchen", text: "Hi" });
  });
});
