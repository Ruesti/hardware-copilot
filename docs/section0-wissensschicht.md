# §0 — Interview-Gate: Wissens- und Herkunftsschicht

**Arbeitstitel:** offen
**Form:** MCP-Server, läuft neben Konnect. Kein eigener Editor, keine eigene App.
**Zweck:** Hinweise zu Schaltungs- und Layout-Entscheidungen geben — und dabei sichtbar machen, worauf jeder Hinweis beruht.

---

## Regel für diese Phase

Keine Implementierung vor Abschluss von §0. Antworten werden hier eingetragen, nicht im Chat gelassen. Offene Punkte bleiben offen markiert statt geraten.

Abschluss von §0 ist erreicht, wenn Block A–F beantwortet sind und das Datenschema aus Block B/C an zwanzig real eingetragenen Regeln getestet wurde.

---

## Block A — Abgrenzung

**A1.** Was macht dieser Server, das Konnect nicht macht? In einem Satz, ohne „und".

> **Antwort:** Er kennzeichnet jeden Schaltungs- oder Layout-Hinweis mit seiner Herkunftsstufe.
> Der Kern ist die Ehrlichkeit der Aussagen — Hinweise gibt es anderswo auch, aber nirgends mit belegt/verifiziert/Vermutung.

**A2.** Was übernimmt Konnect, das hier ausdrücklich nicht nachgebaut wird? (Schaltplan-Edits, ERC/DRC, Exporte, JLCPCB-Suche, Referenzschaltungen — welche davon bleiben dort?)

> **Antwort:** Bei Konnect bleiben Schaltplan-Edits, ERC/DRC, Exporte, JLCPCB-Suche.
> Referenzschaltungen wandern in die Wissensschicht — sie haben Wissenscharakter und gehören zur Regelbasis.

**A3.** Greift der Server lesend auf das KiCad-Projekt zu, oder bekommt er den Kontext vom Modell erzählt? Wenn lesend: welche Dateien, und was passiert bei fehlendem Projekt?

> **Antwort:** Hybrid. Phase 2 startet mit erzähltem Kontext — das Modell beschreibt die Schaltung in der Anfrage, der Server bleibt zustandslos.
> Lesender Zugriff auf das KiCad-Projekt kommt erst, wenn Verified Blocks am Projekt verankert werden müssen (Phase 4, siehe D3).
> Bei fehlendem Projekt laufen Regel-Abfragen ohne Projektbezug weiter.

**A4.** Was ist ausdrücklich nicht Ziel dieser Phase? (Kandidaten: Inventar-Abgleich, BOM, Preisdaten, Platzierung, Routing, UI)

> **Antwort:** Ausdrücklich nicht Ziel: Platzierung und Routing als Ausführung (Layout-*Hinweise* bleiben gerade Zweck des Servers) sowie eine eigene UI (kein Editor, keine App — Ausgabe nur über MCP).
> **Offen:** Inventar-Abgleich, BOM, Preisdaten — nicht ausdrücklich ausgeschlossen, Entscheidung vertagt.

---

## Block B — Regelbasis

**B1.** Welche Felder hat eine Regel? Vorschlag als Ausgangspunkt: Aussage, Begründung, Quelle, Geltungsbereich, Stärke. Was fehlt, was ist überflüssig?

**B2.** Wie wird *Geltungsbereich* ausgedrückt, sodass er maschinell prüfbar ist? („gilt für Schaltregler über 500 kHz" ist Prosa — was ist die strukturierte Form?)

**B3.** Was zählt als Quelle? Datenblatt mit Seitenzahl, Herstellerapplikationsschrift, IPC-Norm, Video mit Zeitmarke — und was davon reicht für die Stufe *belegt*?

**B4.** Woher kommen die ersten Regeln konkret? Welche fünf Bereiche zuerst, und aus welchen Dokumenten?

**B5.** Wie werden Regeln eingetragen? Von Hand in Markdown/TOML, über ein Tool des Servers, oder halbautomatisch aus Dokumenten mit anschließender Freigabe?

**B6.** Was passiert bei widersprüchlichen Regeln? Wer gewinnt, und wird der Widerspruch sichtbar gemacht?

---

## Block C — Klassifikation

Das ist der Kern. Hier keine schnellen Antworten.

**C1.** Die drei Stufen — belegt, verifiziert, Vermutung. Sind das die richtigen drei? Fehlt eine (z. B. *widerlegt*)?

**C2.** Wie kommt ein Hinweis zu seiner Stufe? Trägt der Server sie zu, oder klassifiziert das Modell sich selbst? Bei Selbstklassifikation: was hindert es daran, sich hochzustufen?

**C3.** Ein Hinweis kombiniert eine belegte Regel mit einer Herleitung auf den konkreten Fall. Welche Stufe bekommt er? (Diese Frage entscheidet, ob das System ehrlich bleibt.)

**C4.** Wie sieht *Vermutung* in der Ausgabe aus, sodass sie beim Überfliegen nicht wie die anderen wirkt? Formulierung allein reicht nicht.

**C5.** Kann ein Hinweis die Stufe wechseln? Unter welcher Bedingung wird aus Vermutung *verifiziert* — und wer löst das aus?

**C6.** Was gibt der Server aus, wenn er zu einer Frage nichts Belegtes hat? Schweigen, Vermutung mit Warnung, oder Rückfrage?

---

## Block D — Verified Blocks

**D1.** Was ist ein Block — ein Schaltungsteil, ein Netzabschnitt, eine Kombination aus Bauteilen und Werten? Woran wird er wiedererkannt?

**D2.** Welche Felder werden beim Verifizieren erfasst? (Kandidaten: was gebaut, was gemessen, was nicht funktioniert hat, Fallback, Datum, Projektbezug)

**D3.** Wie hängt ein Block am KiCad-Projekt? Pfad, UUID, kopierter Ausschnitt?

**D4.** Ein Block ist in *deinem* Aufbau verifiziert. Was macht das System, wenn der nächste Fall ähnlich, aber nicht gleich ist?

**D5.** Wird das Schema jetzt gebaut, obwohl die erste Platine erst in drei Monaten kommt? Falls ja: wie wird verhindert, dass es an Annahmen statt an echten Fällen entworfen wird?

---

## Block E — Fragen statt Antworten

**E1.** Welche Bereiche gelten als heikel und bekommen eine Frage statt einer Anweisung? Erste Liste festlegen.

**E2.** Wodurch wird das ausgelöst — Bauteilklasse, Netztopologie, Schlüsselwort im Prompt, manuelle Markierung?

**E3.** Wie sieht eine gute Frage aus? Zwei, drei echte Beispiele ausformulieren, sonst wird es Floskel.

**E4.** Wird zur Frage eine Fundstelle mitgeliefert, wo man nachliest? Woher kommt die?

---

## Block F — Ausgabe und Werkzeuge

**F1.** Welche MCP-Tools bietet der Server? Erste Liste mit Zweck, nicht mit Signatur.

**F2.** Wird der Server gefragt, oder meldet er sich? Rein auf Abruf durch das Modell, oder gibt es eine Prüfung über einen ganzen Schaltplan?

**F3.** In welchem Format kommt ein Hinweis zurück, sodass Stufe, Begründung und Quelle in Claude Code lesbar bleiben?

**F4.** Wie wird der Kontextverbrauch begrenzt? (Konnect lädt Toolsets auf Abruf — was ist hier das Äquivalent?)

**F5.** Wo liegen Regelbasis und Blöcke? Lokal, versioniert im Git, pro Projekt oder global?

---

## Nach §0

**Phase 1 — Schema und zwanzig Regeln.**
Datenmodell für Regel und Klassifikation, zwanzig Regeln von Hand eingetragen, kein Server, keine Tools.
*Gate:* Trennt sich *belegt* von *Vermutung* an allen zwanzig sauber? Wenn nicht, zurück zu Block C.

**Phase 2 — Server mit Abfrage.**
MCP-Server, Regeln abfragbar, Ausgabeformat mit Stufe. Nur lesend.
*Gate:* Ein realer Schaltungsausschnitt liefert Hinweise, die stimmen und deren Stufen ehrlich sind.

**Phase 3 — Vergleichstest.**
Zwanzig bis dreißig Vergleiche gegen Referenzdesigns. Jede Lücke wird eine Regel mit Quelle.
*Gate:* Dokumentierte Grenze — bei welcher Art Frage kippt der Rat.

**Phase 4 — Verified Blocks.**
Erfassung fertig, bevor der Split-Flap-Controller gebaut wird.

**BERICHT** nach jeder Phase: was gebaut, was getestet, was offen, welche Annahme sich als falsch erwiesen hat.
