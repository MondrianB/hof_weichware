# FileMaker-Umbau, Teil 1: Termintabelle, Freigabe und Doppelbuchungsschutz

Schritt-für-Schritt-Anleitung für FileMaker Pro 19 (deutsche Oberfläche).
Gehört zu Abschnitt 8, Schritte 1 bis 6 in `01_Analyse_und_Bauplan.md`.

Zeitbedarf: etwa 1 bis 2 Stunden. Alte Tabellen und Layouts bleiben in diesem Teil
**unverändert**, es wird nur Neues hinzugefügt. Sie können also jederzeit abbrechen.

---

## Schritt 0: Sicherung

1. **Datei → Kopie speichern unter…**
2. Typ: **Kopie der aktuellen Datei**, Name z. B. `Verwaltungssoftware_Sicherung_2026-11-01.fmp12`.

## Schritt 1: Schlüsselfelder prüfen

Die neuen Verknüpfungen brauchen in jeder Tabelle ein eindeutiges, **bei allen Datensätzen
gefülltes** Schlüsselfeld.

| Tabelle | Schlüsselfeld | Hinweis |
|---|---|---|
| `A_Veranstaltungsräume` | `Primärschlüssel` | ist vorhanden |
| `A_Adressdatenbank` | `Ankerschlüssel` | Diese Tabelle hat **kein** Feld `Primärschlüssel`. `Ankerschlüssel` (`Hole ( UUID )`) übernimmt diese Rolle. |

**Prüfen, ob alte Datensätze einen Schlüssel haben** (wurde das Feld nachträglich angelegt,
sind ältere Datensätze leer):

1. Layout `A_Adressdatenbank` öffnen, **Suchenmodus** (⌘F).
2. In das Feld `Ankerschlüssel` ein `=` eintragen (bedeutet „leer“), **Suche starten**.
3. Werden Datensätze gefunden: in das Feld `Ankerschlüssel` klicken, **Datensätze → Feldinhalt ersetzen…**,
   **Durch Formelergebnis ersetzen**: `Hole ( UUID )` → **Ersetzen**.
4. Dasselbe für `A_Veranstaltungsräume` mit dem Feld `Primärschlüssel`.

Liegt das Feld nicht auf dem Layout, legen Sie es vorübergehend im Layoutmodus darauf.

## Schritt 2: Wertelisten anlegen

**Datei → Verwalten → Wertelisten… → Neu**

| Name | Werte (je Zeile einer, „Eigene Werte verwenden“) |
|---|---|
| `Status` | angefragt, bestätigt, abgelehnt, storniert |
| `Art` | Vermietung, Konzert, Lehrgang, Intern |
| `Räume_ID` | **Werte aus Feld verwenden**: erstes Feld `A_Veranstaltungsräume::Primärschlüssel`, **zweites Feld anzeigen** `A_Veranstaltungsräume::Raum`, Haken bei **Nur Werte aus zweitem Feld anzeigen**, sortieren nach zweitem Feld |
| `Adressen_ID` | wie oben mit `A_Adressdatenbank::Ankerschlüssel` und zweitem Feld `A_Adressdatenbank::Kombiname` |

Die beiden letzten Listen speichern im Termin die ID, zeigen aber den Namen an.

## Schritt 3: Tabelle „Termine“ anlegen

**Datei → Verwalten → Datenbank… → Register Tabellen**, Name `Termine` → **Erstellen**.
FileMaker legt die Standardfelder (`Primärschlüssel`, Zeitstempel, ErstelltVon …) automatisch an.

Im **Register Felder** (Tabelle `Termine` wählen) diese Felder anlegen:

| Feldname | Typ | Optionen |
|---|---|---|
| `Raum_ID` | Text | Überprüfung: **Kein leerer Wert** |
| `Adresse_ID` | Text | |
| `Titel` | Text | Überprüfung: **Kein leerer Wert** |
| `Art` | Text | Überprüfung: **Element in Werteliste** `Art` |
| `Beginn` | Zeitstempel | Überprüfung: **Kein leerer Wert** |
| `Ende` | Zeitstempel | Überprüfung: **Kein leerer Wert**, zusätzlich **Formel**: `Ende > Beginn`, Meldung „Das Ende muss nach dem Beginn liegen.“ |
| `Einlass` | Zeit | |
| `Status` | Text | Automatische Eingabe → **Daten**: `angefragt`. Überprüfung: **Element in Werteliste** `Status` |
| `Quelle` | Text | Automatische Eingabe → **Daten**: `intern` |
| `Anfrage_Name` | Text | |
| `Anfrage_Email` | Text | |
| `Anfrage_Telefon` | Text | |
| `Anfrage_Nachricht` | Text | |
| `Serie_ID` | Text | |
| `Preis` | Zahl | |
| `Notiz_intern` | Text | |
| `Google_Event_ID` | Text | |
| `Entschieden_am` | Zeitstempel | |
| `Entschieden_von` | Text | |

Dann die **Formelfelder** (Typ **Formel**, Ergebnistyp jeweils angeben):

| Feldname | Ergebnis | Formel | Speicherung |
|---|---|---|---|
| `Raum_ID_bestätigt` | Text | `Wenn ( Status = "bestätigt" ; Raum_ID ; "" )` | **gespeichert** (Standard, nicht ändern) |
| `Datum` | Datum | `HoleDatum ( Beginn )` | gespeichert |
| `Startzeit` | Zeit | `HoleZeit ( Beginn )` | gespeichert |
| `Endzeit` | Zeit | `HoleZeit ( Ende )` | gespeichert |
| `Wochentag` | Text | `WochentagName ( HoleDatum ( Beginn ) )` | gespeichert |
| `KW` | Zahl | `KalenderWoche ( HoleDatum ( Beginn ) )` | gespeichert |
| `Dauer_Stunden` | Zahl | `Runden ( ( Ende - Beginn ) / 3600 ; 2 )` | gespeichert |
| `Konflikt_Anzahl` | Zahl | `Anzahl ( Termine_Konflikt::Primärschlüssel )` | **erst nach Schritt 4 anlegen**, wird automatisch „nicht gespeichert“ |

**Wichtig:** `Raum_ID_bestätigt` muss gespeichert und indiziert sein, sonst funktioniert die
Beziehung in Schritt 4 nicht. Kontrolle: Feld wählen → **Optionen… → Speicherung**:
„Keine Speicherung des Formelergebnisses“ darf **nicht** angehakt sein.

## Schritt 4: Beziehungen

**Datei → Verwalten → Datenbank… → Register Beziehungen**

### 4a. Termine mit Raum und Adresse verbinden
1. Das Tabellenauftreten `Termine` ist schon da (wurde mit der Tabelle angelegt).
2. Feld `Termine::Raum_ID` mit der Maus auf `A_Veranstaltungsräume::Primärschlüssel` ziehen.
3. Feld `Termine::Adresse_ID` auf `A_Adressdatenbank::Ankerschlüssel` ziehen.

### 4b. Selbstbeziehung für den Doppelbuchungsschutz
1. Unten links auf **Tabelle hinzufügen** (Symbol mit Tabelle und +) klicken.
2. Tabelle `Termine` wählen, Name: `Termine_Konflikt` → OK.
3. `Termine::Raum_ID` auf `Termine_Konflikt::Raum_ID_bestätigt` ziehen.
4. **Doppelklick** auf das Kästchen in der Mitte der neuen Linie. Im Fenster drei weitere Zeilen
   hinzufügen (Felder links und rechts wählen, Operator in der Mitte, dann **Hinzufügen**):

| Termine | Operator | Termine_Konflikt |
|---|---|---|
| `Raum_ID` | `=` | `Raum_ID_bestätigt` |
| `Beginn` | `<` | `Ende` |
| `Ende` | `>` | `Beginn` |
| `Primärschlüssel` | `≠` | `Primärschlüssel` |

5. OK. Jetzt zurück ins Register **Felder** und dort `Konflikt_Anzahl` anlegen (siehe Tabelle oben).

## Schritt 5: Layouts

### 5a. Layout „Termine“ (Bearbeiten eines Termins)
1. **Layouts → Neues Layout/Bericht…**, Kontext: **Termine**, Name `Termine`, Typ **Computer → Formular**.
2. Felder auflegen. Dabei die Steuerelemente einstellen (Feld wählen → **Inspektor → Daten**):
   - `Raum_ID`: **Einblendmenü**, Werteliste `Räume_ID`
   - `Adresse_ID`: **Einblendmenü** oder **Dropdown-Liste**, Werteliste `Adressen_ID`
   - `Art`: Einblendmenü, Werteliste `Art`
   - `Status`: Einblendmenü, Werteliste `Status`
   - `Beginn`, `Ende`: Eingabefelder mit **Kalenderauswahl** anzeigen
3. Ein Textfeld mit Hinweis anlegen, der nur bei Konflikt sichtbar ist: Text „⚠ Raum ist zu dieser
   Zeit bereits belegt“, dann im **Inspektor → Position → Ausblenden, wenn**:
   `Termine::Konflikt_Anzahl = 0`

### 5b. Layout „Anfragen“ (offene Anfragen bearbeiten)
1. **Neues Layout/Bericht**, Kontext **Termine**, Name `Anfragen`, Typ **Liste**.
2. Felder: `Datum`, `Startzeit`, `Endzeit`, `A_Veranstaltungsräume::Raum`, `Titel`, `Anfrage_Name`,
   `Anfrage_Email`, `Konflikt_Anzahl`.
3. Zwei Tasten in den Datenbereich: **„Freigeben“** → Skript `Termin freigeben`,
   **„Ablehnen“** → Skript `Termin ablehnen` (Skripte siehe Schritt 6).

## Schritt 6: Skripte

**Skripte → Script Workspace…** (⌘⇧S). Neues Skript, Schritte von links per Doppelklick einfügen.
Der Text hinter `#` ist ein Kommentar (Skriptschritt **# (Kommentar)**), Sie können ihn weglassen.

### Skript „Anfragen anzeigen“
```
Gehe zu Layout [ "Anfragen" ]
Suchen-Modus aktivieren [ Pause: Aus ]
Feldwert setzen [ Termine::Status ; "angefragt" ]
Ergebnismenge suchen [ ]
Wenn [ Hole ( LetzteFehlerNr ) = 401 ]
    Eigenes Dialogfeld anzeigen [ "Anfragen" ; "Keine offenen Anfragen." ]
    Alle Datensätze anzeigen
Ende (wenn)
Datensätze sortieren [ Beginn aufsteigend ; Ohne Dialog ]
```
Vor `Ergebnismenge suchen` den Schritt **Fehleraufzeichnung setzen [ Ein ]** einfügen, damit bei
„nichts gefunden“ kein FileMaker-Dialog erscheint.

### Skript „Termin freigeben“
```
Datensatz/Abfrage übernehmen [ Ohne Dialog ]
Wenn [ Termine::Konflikt_Anzahl > 0 ]
    Eigenes Dialogfeld anzeigen [ "Raum belegt" ; "Der Raum ist in diesem Zeitraum bereits durch einen bestätigten Termin belegt." ]
    Aktuelles Skript verlassen [ Text-Ergebnis: 0 ]
Ende (wenn)
Feldwert setzen [ Termine::Status ; "bestätigt" ]
Feldwert setzen [ Termine::Entschieden_am ; Hole ( SystemZeitstempel ) ]
Feldwert setzen [ Termine::Entschieden_von ; Hole ( KontoName ) ]
Datensatz/Abfrage übernehmen [ Ohne Dialog ]
Aktuelles Skript verlassen [ Text-Ergebnis: 1 ]
```

### Skript „Termin ablehnen“
```
Eigenes Dialogfeld anzeigen [ "Ablehnen" ; "Anfrage „" & Termine::Titel & "“ wirklich ablehnen?" ; Taste 1: "Ablehnen" ; Taste 2: "Abbrechen" ]
Wenn [ Hole ( LetzteNachrichtenwahl ) ≠ 1 ]
    Aktuelles Skript verlassen [ ]
Ende (wenn)
Feldwert setzen [ Termine::Status ; "abgelehnt" ]
Feldwert setzen [ Termine::Entschieden_am ; Hole ( SystemZeitstempel ) ]
Feldwert setzen [ Termine::Entschieden_von ; Hole ( KontoName ) ]
Datensatz/Abfrage übernehmen [ Ohne Dialog ]
```

### Skript „Termin prüfen“ (Schutz beim direkten Bearbeiten)
```
Wenn [ Termine::Status = "bestätigt" und Termine::Konflikt_Anzahl > 0 ]
    Eigenes Dialogfeld anzeigen [ "Raum belegt" ; "Speichern nicht möglich: Der Raum ist zu dieser Zeit bereits belegt. Bitte Zeit oder Raum ändern oder den Status auf „angefragt“ setzen." ]
    Aktuelles Skript verlassen [ Text-Ergebnis: Falsch ]
Ende (wenn)
Aktuelles Skript verlassen [ Text-Ergebnis: Wahr ]
```

Als Trigger einrichten: Layout `Termine` öffnen → **Layoutmodus** → **Layouts → Layout-Einrichtung…
→ Register Skript-Trigger** → **BeiDatensatzÜbernahme** (engl. *OnRecordCommit*) anhaken →
Skript `Termin prüfen` wählen, Modus **Blättern** angehakt lassen.
Das Ergebnis „Falsch“ verhindert das Speichern.

## Schritt 7: Testen

Legen Sie im Layout `Termine` von Hand an:

| Nr. | Raum | Beginn | Ende | Status | Erwartung |
|---|---|---|---|---|---|
| 1 | Tenne | morgen 10:00 | morgen 12:00 | bestätigt | wird gespeichert |
| 2 | Tenne | morgen 11:00 | morgen 13:00 | angefragt | wird gespeichert, Hinweis „bereits belegt“ erscheint |
| 3 | Tenne | morgen 12:00 | morgen 14:00 | bestätigt | wird gespeichert (schließt direkt an) |
| 4 | Scheune | morgen 10:00 | morgen 12:00 | bestätigt | wird gespeichert (anderer Raum) |

Dann:
- Termin 2 über **Anfragen → Freigeben**: Es erscheint die Meldung „Raum belegt“, der Status bleibt „angefragt“.
- In Termin 2 den Status von Hand auf „bestätigt“ stellen und den Datensatz verlassen: Es erscheint die Meldung, Speichern wird verhindert.
- Termin 2 auf 14:00 bis 16:00 Uhr verschieben, dann **Freigeben**: Das klappt.
- Termin 1 auf 11:00 bis 15:00 Uhr verlängern: Das wird verhindert, weil Termin 3 im Weg ist.

Wenn ein Test anders ausgeht, melden Sie sich mit der Nummer des Tests und der Meldung, die erschienen ist.

## Wie es danach weitergeht

- Teil 2: Bestehende Termine aus den drei alten Kalendern übernehmen (Import und Hilfsskript)
- Teil 3: Serientermine (korrigiertes Skript), Veranstaltungsplanung und Einsätze
- Teil 4: Google-Kalender-Abgleich
