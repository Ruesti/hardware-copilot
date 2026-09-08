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

> **Antwort:** Der Basisvorschlag plus drei Ergänzungen. Felder einer Regel:
> - **Aussage** — die Regel selbst
> - **Begründung** — warum sie gilt
> - **Quelle** — mit präziser Fundstelle (siehe B3)
> - **Geltungsbereich** — strukturiert (siehe B2)
> - **Stärke** — Verbindlichkeit: muss / sollte / kann
> - **ID** — eindeutig, referenzierbar aus Hinweisen und Verified Blocks
> - **Datum** — Eintrag und letzte Prüfung; Quellen altern, Datenblatt-Revisionen ändern sich
> - **Stufe** — belegt / verifiziert / Vermutung, direkt an der Regel gespeichert
> - **Ausnahmen/Grenzen** — wann die Regel *nicht* gilt; verhindert Übergeneralisierung durch das Modell

**B2.** Wie wird *Geltungsbereich* ausgedrückt, sodass er maschinell prüfbar ist? („gilt für Schaltregler über 500 kHz" ist Prosa — was ist die strukturierte Form?)

> **Antwort:** Bedingungsfelder — definierte Achsen als strukturierte Felder: Bauteilklasse, Parameterbereich, Netztyp (z. B. `klasse=schaltregler`, `f_schalt>=500kHz`). Prüfbar per Feldvergleich. Das Achsen-Schema wird nicht vorab entworfen, sondern wächst mit den zwanzig Testregeln aus Phase 1.

**B3.** Was zählt als Quelle? Datenblatt mit Seitenzahl, Herstellerapplikationsschrift, IPC-Norm, Video mit Zeitmarke — und was davon reicht für die Stufe *belegt*?

> **Antwort:** Strenge Linie: *belegt* erfordert eine Primärquelle — Datenblatt mit Seitenzahl, Hersteller-Applikationsschrift oder Norm (IPC/JEDEC). Videos, Blogs und Bücher zählen als Quelle, tragen aber höchstens die Stufe *Vermutung* — auch dann mit präziser Fundstelle (Zeitmarke, Seite).

**B4.** Woher kommen die ersten Regeln konkret? Welche fünf Bereiche zuerst, und aus welchen Dokumenten?

> **Antwort:** Fünf Bereiche:
> 1. **Entkopplung & Masseführung** — Abblockkondensatoren, Rückstromwege, Ground-Konzept. Quellen: TI/Murata-Applikationsschriften, Espressif Hardware Design Guidelines.
> 2. **Schaltregler-Layout** — Hot Loop, Feedback-Pfad, Induktivität-Platzierung. Quellen: TI/Analog-Devices-Applikationsschriften zum jeweiligen Regler-IC.
> 3. **ESP32-spezifisch** — Antennen-Keepout, Strom-Peaks beim WLAN-Senden, Strapping-Pins. Quelle: Espressif Hardware Design Guidelines.
> 4. **Motortreiber & induktive Lasten** — Freilaufdioden, Treiber-Layout, Stromspitzen (Split-Flap-Controller). Quellen: Treiber-Datenblätter (z. B. ULN2003, DRV8825).
> 5. **Verpolschutz & Versorgung** — Verpolschutz, Inrush, Sicherungen, Stecker-Pinning. Quellen: Hersteller-Applikationsschriften (TI, ROHM).

**B5.** Wie werden Regeln eingetragen? Von Hand in Markdown/TOML, über ein Tool des Servers, oder halbautomatisch aus Dokumenten mit anschließender Freigabe?

> **Antwort:** Von Hand in TOML/Markdown, als Dateien im Git — diffbar und reviewbar. Phase 1 läuft ohnehin ohne Server. Ein Eintrags-Tool kann später kommen, wenn sich das Schema bewährt hat.

**B6.** Was passiert bei widersprüchlichen Regeln? Wer gewinnt, und wird der Widerspruch sichtbar gemacht?

> **Antwort:** Niemand gewinnt. Der Server zeigt beide Regeln samt Quellen und markiert den Widerspruch ausdrücklich. Keine automatische Auflösung — konsequenteste Fortsetzung von A1: Ehrlichkeit vor Bequemlichkeit.

---

## Block C — Klassifikation

Das ist der Kern. Hier keine schnellen Antworten.

**C1.** Die drei Stufen — belegt, verifiziert, Vermutung. Sind das die richtigen drei? Fehlt eine (z. B. *widerlegt*)?

> **Antwort:** Drei reichen. Jede weitere Stufe verwässert. Widerlegtes wird keine eigene Stufe — es fliegt aus der Regelbasis oder landet im Ausnahmen-Feld der Regel (B1), wenn das Scheitern selbst informativ ist.

**C2.** Wie kommt ein Hinweis zu seiner Stufe? Trägt der Server sie zu, oder klassifiziert das Modell sich selbst? Bei Selbstklassifikation: was hindert es daran, sich hochzustufen?

> **Antwort:** Das Modell schlägt vor, der Server prüft. Der Server validiert die vorgeschlagene Stufe gegen die Regelbasis und darf dabei nur **abstufen, nie hochstufen**. Die Obergrenze eines Hinweises ist die in den Daten gespeicherte Stufe der zitierten Regel (B1) — Hochstufen ist damit strukturell begrenzt, nicht bloß verboten.

**C3.** Ein Hinweis kombiniert eine belegte Regel mit einer Herleitung auf den konkreten Fall. Welche Stufe bekommt er? (Diese Frage entscheidet, ob das System ehrlich bleibt.)

> **Antwort:** Zweiteilige Ausgabe. Der Hinweis wird aufgespalten: „Regel (belegt): …" und „Anwendung auf deinen Fall (Vermutung): …". Keine Mischstufe — die Herkunft jeder Teilaussage bleibt einzeln sichtbar. Zusammen mit C2 heißt das: Anwendungs-Teile können strukturell nie über *Vermutung* hinaus; nur der Regel-Teil trägt die Stufe aus den Daten.

**C4.** Wie sieht *Vermutung* in der Ausgabe aus, sodass sie beim Überfliegen nicht wie die anderen wirkt? Formulierung allein reicht nicht.

> **Antwort:** Pflicht-Marker je Hinweis. Jeder Hinweis trägt eine Stufen-Zeile; Vermutungen zusätzlich ein Präfix (⚠ VERMUTUNG) und explizit „Quelle: keine". Die Reihenfolge der Hinweise bleibt thematisch, die Kennzeichnung hängt am Hinweis selbst.

**C5.** Kann ein Hinweis die Stufe wechseln? Unter welcher Bedingung wird aus Vermutung *verifiziert* — und wer löst das aus?

> **Antwort:** Ja, aber immer durch den Menschen und immer an der Regel (die Stufe ist ein Feld der Regel, B1):
> - Vermutung → **verifiziert:** ein real vermessener Aufbau wird als Verified Block eingetragen (D2).
> - Vermutung → **belegt:** eine Primärquelle wird nachträglich gefunden und an der Regel eingetragen (B3-Maßstab).
> Der Server stuft nie selbst um.

**C6.** Was gibt der Server aus, wenn er zu einer Frage nichts Belegtes hat? Schweigen, Vermutung mit Warnung, oder Rückfrage?

> **Antwort:** Lücke benennen und protokollieren. Ausgabe: „Keine belegte Regel zu X vorhanden." Zusätzlich landet die unbeantwortete Frage in einer Lücken-Liste — jeder Eintrag ist Kandidat für eine neue Regel mit Quelle. Das ist dieselbe Mechanik, mit der Phase 3 Lücken in Regeln verwandelt.

---

## Block D — Verified Blocks

**D1.** Was ist ein Block — ein Schaltungsteil, ein Netzabschnitt, eine Kombination aus Bauteilen und Werten? Woran wird er wiedererkannt?

> **Antwort:** Eine konkrete Bauteil-Kombination mit Werten — Kernbauteil plus umgebende Bauteile (z. B. Regler-IC mit Ein-/Ausgangskondensatoren). Wiedererkannt wird er über Kernbauteil und Topologie. Eng gefasst, dafür präzise prüfbar.

**D2.** Welche Felder werden beim Verifizieren erfasst? (Kandidaten: was gebaut, was gemessen, was nicht funktioniert hat, Fallback, Datum, Projektbezug)

> **Antwort:** Die sechs Kandidaten plus drei Ergänzungen:
> - **Gebaut** — was aufgebaut wurde
> - **Gemessen** — die Messwerte
> - **Gescheitert** — was nicht funktioniert hat
> - **Fallback** — was stattdessen trug
> - **Datum**
> - **Projektbezug**
> - **Messbedingungen** — womit und wie gemessen (Multimeter vs. Oszilloskop, Last, Temperatur); bestimmt, wie belastbar *verifiziert* ist
> - **Getestete Grenzen** — bis wohin vermessen (max. Last, Frequenz, Dauer); Gegenstück zum Ausnahmen-Feld der Regeln (B1), Grundlage für D4
> - **Revision/Bestückung** — Platinen-Revision und Bestückungsvariante

**D3.** Wie hängt ein Block am KiCad-Projekt? Pfad, UUID, kopierter Ausschnitt?

> **Antwort:** Kopierter Ausschnitt. Der Block speichert eine eigene Kopie des vermessenen Teilschaltbilds (Auszug/Netzliste) plus lose Referenz aufs Projekt. Begründung: Verifiziert ist ein *Stand*, keine Datei — das Projekt entwickelt sich nach der Messung weiter, ein Pfad zeigte irgendwann auf etwas anderes als das Vermessene.

**D4.** Ein Block ist in *deinem* Aufbau verifiziert. Was macht das System, wenn der nächste Fall ähnlich, aber nicht gleich ist?

> **Antwort:** Immer Vermutung plus Differenzliste. Der Block wird als Referenz gezeigt („in Aufbau X verifiziert"), aber der Hinweis für den neuen Fall trägt die Stufe *Vermutung*, und die Abweichungen werden explizit aufgezählt. Konsistent mit C3: Übertragung ist Herleitung.

**D5.** Wird das Schema jetzt gebaut, obwohl die erste Platine erst in drei Monaten kommt? Falls ja: wie wird verhindert, dass es an Annahmen statt an echten Fällen entworfen wird?

> **Antwort:** Ja, jetzt — parallel zum Regel-Schema in Phase 1. Das Risiko, an Annahmen statt an echten Fällen zu entwerfen, wird nicht verhindert, sondern bewusst getragen: Das Schema gilt bis zur ersten Platine als **vorläufig**, eine Revision nach den ersten echten Verified Blocks (Split-Flap-Controller) ist fest eingeplant und kein Scheitern.

---

## Block E — Fragen statt Antworten

**E1.** Welche Bereiche gelten als heikel und bekommen eine Frage statt einer Anweisung? Erste Liste festlegen.

> **Antwort:** Erste Liste, vier Bereiche:
> 1. **Netzspannung** — alles über Schutzkleinspannung: 230 V, Netzteile, galvanische Trennung. Falsche Anweisung = Lebensgefahr.
> 2. **Akku-Laden & Schutz** — LiPo/Li-Ion-Laden, Ladeschluss, Tiefentladung, Temperaturüberwachung. Brandgefahr.
> 3. **Hochstrom & Thermik** — Leiterbahn-Strombelastbarkeit, Sicherungen, Kühlung, Motorströme.
> 4. **Funk & Zertifizierung** — Antennen-Anpassung, Abstrahlung, CE/Funkzulassung. Fehler sind teuer und schwer rückholbar.

**E2.** Wodurch wird das ausgelöst — Bauteilklasse, Netztopologie, Schlüsselwort im Prompt, manuelle Markierung?

> **Antwort:** Doppelt abgesichert:
> - Bereiche und Regeln tragen ein **Heikel-Flag** in der Regelbasis.
> - Zusätzlich greifen **strukturelle Schwellen** aus den Bedingungsfeldern (B2) unabhängig von vorhandenen Regeln — z. B. Spannung > 50 V, Bauteilklasse Akku-Lader.
> So löst auch eine Lücke (C6) im heiklen Bereich eine Frage aus, nicht nur eine getroffene Regel.

**E3.** Wie sieht eine gute Frage aus? Zwei, drei echte Beispiele ausformulieren, sonst wird es Floskel.

> **Antwort:** Stil: *Entscheidung mit Optionen* — die Frage stellt die offene Design-Entscheidung mit ihren Wegen dar, ohne einen zu wählen. Beispiele:
>
> > „Soll die 230-V-Seite auf dieser Platine liegen oder in einem fertigen Netzteil-Modul? Auf der Platine: Kriechstrecken nach IPC-2221 einhalten, Sicherung, Berührschutz. Modul: teurer, aber die Gefahr bleibt gekapselt."
>
> > „Trennst du Motor- und Logik-Masse in einem Punkt oder führst du eine gemeinsame Fläche? Ein Punkt: Rückströme kalkulierbar. Fläche: einfacher, aber Störungen wandern in die Logik."

**E4.** Wird zur Frage eine Fundstelle mitgeliefert, wo man nachliest? Woher kommt die?

> **Antwort:** Pflicht, wenn vorhanden. Die Fundstelle kommt aus der Quelle der auslösenden Regel (B3: Datenblatt mit Seite, Applikationsschrift, Norm). Existiert keine Regel — Lücke im heiklen Bereich — kommt die Frage ohne Fundstelle, ehrlich als solche markiert, und die Lücke landet im Protokoll (C6).

---

## Block F — Ausgabe und Werkzeuge

**F1.** Welche MCP-Tools bietet der Server? Erste Liste mit Zweck, nicht mit Signatur.

> **Antwort:** Vier Gruppen:
> 1. **Abfrage-Kern** — Regeln zu einem beschriebenen Fall abrufen (Match über die Bedingungsfelder, B2); eine Quelle im Volltext nachschlagen. Das Minimum für Phase 2.
> 2. **Klassifikations-Prüfung** — das Modell reicht seinen Hinweis-Entwurf ein, der Server prüft die Stufen und darf nur abstufen (C2). Macht die Zweiteilung aus C3 erzwingbar statt vereinbart.
> 3. **Lücken-Werkzeuge** — Lücke protokollieren, Lückenliste abrufen (C6); füttert die Phase-3-Mechanik.
> 4. **Verified-Block-Werkzeuge** — Block erfassen, Blöcke durchsuchen (D2); gebaut in Phase 4.

**F2.** Wird der Server gefragt, oder meldet er sich? Rein auf Abruf durch das Modell, oder gibt es eine Prüfung über einen ganzen Schaltplan?

> **Antwort:** Rein auf Abruf. Das Modell fragt, der Server antwortet — mehr nicht. Passt zu Phase 2 („nur lesend") und hält den Server aus Abläufen heraus, die er nicht versteht. Eine Ganzplan-Prüfung oder automatische Auslösung ist damit nicht beschlossen; falls später gewünscht, ist es eine neue Entscheidung nach Phase 4.

**F3.** In welchem Format kommt ein Hinweis zurück, sodass Stufe, Begründung und Quelle in Claude Code lesbar bleiben?

> **Antwort:** Markdown mit eingebettetem JSON. Oben der lesbare Block mit festen Zeilen — das Modell soll ihn unverändert durchreichen statt umformulieren —, darunter die Rohdaten als JSON für spätere Werkzeuge. Redundant, aber robust. Beispiel:
>
> ```markdown
> ### Hinweis — Eingangskondensator
> **Stufe: BELEGT**
> Regel R-023: Eingangskondensator < 5 mm an VIN.
> Begründung: Hot-Loop-Fläche bestimmt die Abstrahlung.
> Quelle: TI SLVA773, S. 4 | Geltung: klasse=schaltregler
>
> **Anwendung auf deinen Fall — ⚠ VERMUTUNG**
> Beim TPS5430 heißt das: C3 direkt an Pin 7.
> Quelle: keine (Herleitung)
> ```
> ```json
> {"regel": {"id": "R-023", "stufe": "belegt", "quelle": "TI SLVA773 S.4"},
>  "anwendung": {"stufe": "vermutung", "quelle": null}}
> ```

**F4.** Wie wird der Kontextverbrauch begrenzt? (Konnect lädt Toolsets auf Abruf — was ist hier das Äquivalent?)

> **Antwort:** Zweistufige Detailtiefe. Abfragen liefern zuerst die Kurzform (ID, Aussage, Stufe); Begründung, Quelle und Geltung im Volltext kommen nur per Nachfass-Tool mit Regel-ID — das Äquivalent zu Konnects Abruf-Prinzip.

**F5.** Wo liegen Regelbasis und Blöcke? Lokal, versioniert im Git, pro Projekt oder global?

> **Antwort:** Global, in einem eigenen Wissens-Repo im Git. Regeln gelten projektübergreifend; Verified Blocks liegen ebenfalls dort und tragen ihren Projektbezug als Feld (D2). Die Historie jeder Regeländerung — einschließlich Stufenwechsel (C5) — bleibt nachvollziehbar.

---

## Nach §0

**Phase 1 — Schema und zwanzig Regeln.**
Datenmodell für Regel und Klassifikation, zwanzig Regeln von Hand eingetragen, kein Server, keine Tools.
*Gate:* Trennt sich *belegt* von *Vermutung* an allen zwanzig sauber? Wenn nicht, zurück zu Block C.

> **Ergebnis (2026-09-08): Gate BESTANDEN.** Repo `hardware-wissen` (lokal, `~/projects/hardware-wissen`): TOML-Schema nach B1/B2, 20 Regeln in den fünf B4-Bereichen — 15 × belegt (TI, Espressif, Nichicon, Littelfuse; alle mit PDF-Seite und selbst geprüftem Wortzitat), 5 × Vermutung. Maschineller Gate-Check: Trennung an allen 20 sauber. Details in `BERICHT-PHASE-1.md` dort. **Damit ist §0 abgeschlossen** (Blöcke A–F beantwortet + Schema an zwanzig real eingetragenen Regeln getestet).

**Phase 2 — Server mit Abfrage.**
MCP-Server, Regeln abfragbar, Ausgabeformat mit Stufe. Nur lesend.
*Gate:* Ein realer Schaltungsausschnitt liefert Hinweise, die stimmen und deren Stufen ehrlich sind.

> **Ergebnis (2026-09-08): Gate BESTANDEN.** Server `wissensschicht/` (PR #4, gemergt), 5 Tools, 33 Tests; Gate-Lauf am realen ESP32-S3-Logger-Schaltplan; in Claude Code eingebunden (user-Scope). Details: `docs/BERICHT-PHASE-2-wissensschicht.md`.

**Phase 3 — Vergleichstest.**
Zwanzig bis dreißig Vergleiche gegen Referenzdesigns. Jede Lücke wird eine Regel mit Quelle.
*Gate:* Dokumentierte Grenze — bei welcher Art Frage kippt der Rat.

> **Ergebnis (2026-09-08): Gate ERFÜLLT.** 22 Vergleiche; Regelbasis auf 38 Regeln (34 belegt/4 Vermutung), neue Bereiche akku-laden/ldo/schnittstellen, Achsen chip_familie/topologie; Boost- und S3-Kipp-Punkte live behoben. Grenzen dokumentiert in `GRENZEN.md` (hardware-wissen), Bericht in `BERICHT-PHASE-3.md` dort.

**Block E — Fragen statt Antworten (nachgezogen 2026-09-08):**

> **Umgesetzt.** `heikel.toml` im Wissens-Repo (vier E1-Bereiche, E3-Fragen, E4-Fundstellen), Auslösung per Flag + Schwellen (spannung_v >= 50, strom_a >= 5, Klassen-/Achsen-Trigger). Netzspannung unterdrückt Kleinspannungs-Regeln mit Begründung; Katalog-Validierung gegen still geschluckte Werte. Live verifiziert: 230-V-Abfrage liefert die Frage statt vier BELEGT-Stempeln.

**Phase 4 — Verified Blocks.**
Erfassung fertig, bevor der Split-Flap-Controller gebaut wird.

> **Ergebnis (2026-09-08): ERFÜLLT.** Erfassung gebaut und getestet, bevor die erste Platine existiert: record_block/search_blocks/get_block mit erzwungenem D2-Schema (ohne Messwerte, Messbedingungen, Grenzen, Ausschnitt wird nicht gespeichert), D3-Ausschnitt als eingefrorene Datei, D4-Hinweis in jeder Ausgabe, C5 bleibt beim Menschen. Schema weiterhin vorläufig (D5) — Revision nach den ersten echten Blöcken eingeplant. Bericht: `docs/BERICHT-PHASE-4-wissensschicht.md`.

**BERICHT** nach jeder Phase: was gebaut, was getestet, was offen, welche Annahme sich als falsch erwiesen hat.
