# FileMaker: Analyse und Bauplan für die zusammengeführte Lösung

Grundlage: XML-Export „Verwaltungssoftware Hof Hesselmann.fmp12“ (FileMaker 19.6.3, Stand 31.10.2026)
und die Web-Version in diesem Repository (Raumkalender mit Freigabe und Kalender-Abgleich).

---

## 1. Bestandsaufnahme Ihrer Datei

| Tabelle | Inhalt | Bewertung |
|---|---|---|
| `A_Adressdatenbank` | Adressen mit Adressart, Firma, Kurs, Social Media | **Beibehalten**, wird die zentrale Adresstabelle |
| `Kontaktdaten_Klienten` | Adressen (ältere Fassung) | Doppelt zu `A_Adressdatenbank`, Daten übernehmen, dann entfernen |
| `A_Veranstaltungsräume` | Raum je Zeile mit Mietpreisen und Putzgeld | **Beibehalten**, wird die Raumtabelle |
| `A_ Veranstaltungsräume` | ein Feld je Raum (Scheune, Tenne …) | Ersetzen: Räume als Spalten sind schwer auszuwerten |
| `Terminkalender` | Termine mit Serien (Periodizität, Wiederholungen) | Zusammenführen in **eine** Termintabelle |
| `A_Terminkalender` | Termine mit Einlass, Veranstalter, Raum | Zusammenführen in **eine** Termintabelle |
| `Veranstaltungsmanagement_Terminverwaltung` | Organisation: GEMA, Helfer, Werbung, Getränke, Auf- und Abbau | **Beibehalten** als Veranstaltungsplanung, an Termin gekoppelt |
| `Abrechnungsblatt` | Kassenzählung nach Münzen und Scheinen | **Beibehalten**, an Veranstaltung koppeln |
| `A_Bestandsverzeichnis` | Inventar | Beibehalten (unabhängig) |
| `Versionshistorie` | Änderungsprotokoll | Beibehalten |
| `Rechnungswesen_Vermietung`, `A_Rechnungswesen_Vermietung` | fast leer | Später neu als „Rechnungen“ |
| `Bürgerzentrum Testmodul` | leer | Entfernen |

**Stark an Ihrer Lösung** (in der Web-Version noch nicht vorhanden): Helferplanung, GEMA-Anmeldung,
Werbung, Getränkeverkauf, Kassenabrechnung, Inventar, Mietpreise (normal, reduziert, stundenweise,
Putzgeld), Adressarten, Serientermine.

**Stark an der Web-Version** (in Ihrer Datei noch nicht vorhanden): Status mit Freigabe
(angefragt, bestätigt, abgelehnt, storniert), Schutz vor Doppelbelegung, Termine fest mit Raum
und Adresse verknüpft, Kalender-Abgleich nach außen.

## 2. Auffälligkeiten, die Sie vor dem Umbau kennen sollten

1. **Es gibt keine einzige Beziehung zwischen den Tabellen.** Raum und Veranstalter werden als
   Text eingetragen (z. B. `Raum`, `Kombiname`). Folgen:
   - Wird ein Name geändert (Heirat, Tippfehler), passen alte Termine nicht mehr dazu.
   - Ein Doppelbuchungsschutz ist so nicht möglich.
   - **Lösung:** Verknüpfung über Schlüsselfelder (IDs), siehe Abschnitt 4.
2. **Drei Terminkalender** (`Terminkalender`, `A_Terminkalender`, `Veranstaltungsmanagement_Terminverwaltung`)
   und **zwei Adresstabellen** führen dazu, dass dieselben Daten an mehreren Stellen gepflegt werden.
3. **Defekte Verweise** (Felder oder Tabellen, die gelöscht wurden):
   - Formel `Kontaktdaten_Klienten::Haus_und_Vorname` verweist auf nicht mehr vorhandene Felder.
   - Skript „Taste Neuer Datensatz Kalender“ setzt Felder einer nicht mehr vorhandenen Tabelle.
   - Skript „Klientenindex kopieren“ liest aus einer nicht mehr vorhandenen Tabelle.
   - Ein zweites Layout „HelferInnen_Liste“ zeigt auf eine nicht mehr vorhandene Tabelle.
4. **Skript „multiple Einträge“ kann sich aufhängen:** Ist `Anzahl Wiederholungen` leer oder 0,
   wird `$Schleifendurchgänge` nach dem ersten Durchlauf −1, −2 … und erreicht nie 0. Die Schleife
   läuft endlos und erzeugt immer neue Datensätze. Korrigierte Fassung in Abschnitt 6.
5. **Wiederholfelder für Helfer** (`Helfer Aufbau` usw. mit je 10 Wiederholungen): Man kann nicht
   gut auswerten, wer wie oft geholfen hat, und eine Person ist nur als Text eingetragen.
   Besser: eigene Tabelle „Einsätze“ (Abschnitt 3).
6. Feld `Abstand Tage` ist vom Typ **Text**, wird aber zum Rechnen benutzt. Besser Typ **Zahl**.
7. Raumnamen weichen ab: Ihre Datei nennt „Gruppenraum 1/2 Obergeschoss“, die Web-Version
   „Seminarraum 1/2“. **Bitte festlegen, welcher Name gilt.**

## 3. Zusammengeführtes Datenmodell

Jede Tabelle erhält die FileMaker-Standardfelder (`Primärschlüssel` = `Hole(UUID)`,
Erstellungs- und Änderungszeitstempel, ErstelltVon, GeändertVon). Diese sind unten nicht aufgeführt.
Fremdschlüssel enden auf `_ID`.

### Räume (aus `A_Veranstaltungsräume`)
| Feld | Typ | Hinweis |
|---|---|---|
| Name | Text | Tenne, Scheune, Kaminraum, Modersohn-Raum, Upkammer, Gruppenraum 1, Gruppenraum 2 |
| Kapazität | Zahl | |
| Miete_normal, Miete_reduziert, Miete_Stunde_Kurse, Putzgeld | Zahl | aus Ihrer Tabelle |
| Aktiv | Zahl | 1 = buchbar |
| Sortierung | Zahl | Reihenfolge in Listen und im Kalender |
| Google_Kalender_ID | Text | optional, falls je Raum ein Google-Kalender geführt wird |

### Adressen (aus `A_Adressdatenbank`, ergänzt um `Kontaktdaten_Klienten`)
Alle bisherigen Felder bleiben. Neu ist nur, dass andere Tabellen über `Primärschlüssel`
verknüpfen statt über `Kombiname`. `Kombiname` bleibt als Anzeigefeld.

### Termine (ersetzt die drei Terminkalender)
| Feld | Typ | Hinweis |
|---|---|---|
| Raum_ID | Text | → Räume |
| Adresse_ID | Text | → Adressen (Mieter, Veranstalter, Kursleitung) |
| Titel | Text | |
| Art | Text | Werteliste: Vermietung, Konzert, Lehrgang, Intern |
| Beginn, Ende | Zeitstempel | **ein** Zeitstempel statt Datum und Uhrzeit getrennt, nötig für Überschneidungsprüfung und Google |
| Einlass | Zeit | aus `A_Terminkalender` |
| Status | Text | Werteliste: angefragt, bestätigt, abgelehnt, storniert |
| Quelle | Text | intern oder Google (Anfrage von außen) |
| Anfrage_Name, Anfrage_Email, Anfrage_Telefon, Anfrage_Nachricht | Text | nur für Anfragen von Außenstehenden, die noch keine Adresse haben |
| Serie_ID | Text | gleicher Wert für alle Termine einer Serie |
| Preis | Zahl | später aus Raum und Tarif berechnet |
| Notiz_intern | Text | |
| Google_Event_ID | Text | für den Abgleich (Abschnitt 7) |
| Entschieden_am, Entschieden_von | Zeitstempel, Text | wer hat freigegeben oder abgelehnt |
| Raum_ID_bestätigt | Berechnung (Text, **gespeichert**) | `Wenn ( Status = "bestätigt" ; Raum_ID ; "" )` |
| Datum, Startzeit, Endzeit, Wochentag, KW, Dauer | Berechnungen | nur zur Anzeige: `HoleDatum(Beginn)`, `HoleZeit(Beginn)`, `WochentagName(HoleDatum(Beginn))`, `KalenderWoche(HoleDatum(Beginn))`, `Ende - Beginn` |
| Konflikt_Anzahl | Berechnung (Zahl, nicht gespeichert) | `Anzahl ( Termine_Konflikt::Primärschlüssel )` |

### Veranstaltungsplanung (aus `Veranstaltungsmanagement_Terminverwaltung`)
Alle Planungsfelder bleiben (GEMA, Getränke, Werbung, Auf- und Abbau, Soundcheck …).
Neu ist `Termin_ID` → Termine. Die Felder `Veranstaltung`, `Ort`, `Datum`, `Uhrzeit Beginn/Ende`
entfallen, weil sie vom Termin kommen. Die Wiederholfelder für Helfer und die `wer_…`-Felder werden
durch die Tabelle **Einsätze** ersetzt.

### Einsätze (neu, ersetzt die Wiederholfelder)
| Feld | Typ | Hinweis |
|---|---|---|
| Veranstaltung_ID | Text | → Veranstaltungsplanung |
| Adresse_ID | Text | → Adressen (Werteliste „Kombiname Mithelfende“ wie bisher) |
| Aufgabe | Text | Werteliste: Aufbau, Abbau, Getränke, Kaffee und Kuchen, Tageszeitung, Na dann, Homepage, A3-Plakat, Bauzaunplakat, Social Media, Datenportal Münsterland, Reinigung |
| Erledigt | Text | Werteliste „ja nein noch nicht gemacht“ |

### Abrechnungsblatt
Bleibt wie es ist, `Veranstaltung` (Text) wird durch `Veranstaltung_ID` ersetzt.

### Bestandsverzeichnis, Versionshistorie
Unverändert. Optional im Bestandsverzeichnis `Raum_ID`, um Inventar einem Raum zuzuordnen.

## 4. Beziehungen

```
Räume ──< Termine >── Adressen
              │
              ├──< Termine_Konflikt   (Selbstbeziehung, Doppelbuchungsschutz)
              │
              └──1 Veranstaltungsplanung ──< Einsätze >── Adressen
                                 └──< Abrechnungsblatt
```

| Von | Nach | Bedingung |
|---|---|---|
| Termine | Räume | `Raum_ID = Primärschlüssel` |
| Termine | Adressen | `Adresse_ID = Primärschlüssel` |
| Termine | Veranstaltungsplanung | `Primärschlüssel = Termin_ID` |
| Veranstaltungsplanung | Einsätze | `Primärschlüssel = Veranstaltung_ID` |
| Einsätze | Adressen (Auftreten „Einsatz_Adressen“) | `Adresse_ID = Primärschlüssel` |
| Veranstaltungsplanung | Abrechnungsblatt | `Primärschlüssel = Veranstaltung_ID` |
| **Termine** | **Termine_Konflikt** (zweites Auftreten von Termine) | siehe unten |

**Doppelbuchungsschutz** über die Selbstbeziehung `Termine` → `Termine_Konflikt`, vier Bedingungen:

```
Termine::Raum_ID           =  Termine_Konflikt::Raum_ID_bestätigt
Termine::Beginn            <  Termine_Konflikt::Ende
Termine::Ende              >  Termine_Konflikt::Beginn
Termine::Primärschlüssel   ≠  Termine_Konflikt::Primärschlüssel
```

Damit zeigt `Konflikt_Anzahl` für jeden Termin, wie viele **bestätigte** Termine im selben Raum
sich zeitlich überschneiden. Direkt anschließende Termine (10–12 Uhr und 12–14 Uhr) gelten nicht
als Überschneidung.

## 5. Freigabe-Ablauf

Skript **„Termin freigeben“** (Aufruf über Taste im Layout „Anfragen“):

```
Wenn [ Termine::Konflikt_Anzahl > 0 ]
    Eigenes Dialogfeld anzeigen [ "Raum belegt" ; "Der Raum ist in diesem Zeitraum bereits durch einen bestätigten Termin belegt." ]
    Aktuelles Skript verlassen [ Text-Ergebnis: "Konflikt" ]
Ende (wenn)
Feldwert setzen [ Termine::Status ; "bestätigt" ]
Feldwert setzen [ Termine::Entschieden_am ; Hole ( ZeitstempelUTC ) ]   # oder Hole ( SystemZeitstempel )
Feldwert setzen [ Termine::Entschieden_von ; Hole ( KontoName ) ]
Datensatz/Abfrage übernehmen [ Ohne Dialog ]
# Später: Skript "Google: Termin übertragen" aufrufen (Abschnitt 7)
```

Skript **„Termin ablehnen“**: Status auf „abgelehnt“ setzen, Entschieden_am und Entschieden_von setzen,
übernehmen.

**Schutz auch beim direkten Bearbeiten:** Im Layout „Termine“ den Skript-Trigger
**OnRecordCommit** auf ein Skript „Termin prüfen“ legen:

```
Wenn [ Termine::Status = "bestätigt" und Termine::Konflikt_Anzahl > 0 ]
    Eigenes Dialogfeld anzeigen [ "Raum belegt" ; "Speichern nicht möglich: Der Raum ist bereits belegt." ]
    Aktuelles Skript verlassen [ Text-Ergebnis: Falsch ]   # Falsch verhindert das Speichern
Ende (wenn)
Aktuelles Skript verlassen [ Text-Ergebnis: Wahr ]
```

Für die Ansicht der offenen Anfragen genügt ein Layout „Anfragen“ (Listenansicht auf Termine)
mit der gespeicherten Suche `Status = "angefragt"` und den Tasten „Freigeben“, „Ablehnen“.

## 6. Korrigiertes Skript für Serientermine

Ersetzt „multiple Einträge“. Erwartet den ersten Termin als aktuellen Datensatz sowie
`$$Anzahl` (Anzahl **weiterer** Termine) und `$$AbstandTage` (z. B. 7 für wöchentlich),
z. B. über ein kleines Dialog-Layout oder über Felder mit globaler Speicherung.

```
Variable setzen [ $anzahl ; Wert: Wenn ( IstLeer ( $$Anzahl ) ; 0 ; Abs ( $$Anzahl ) ) ]
Variable setzen [ $abstand ; Wert: Wenn ( IstLeer ( $$AbstandTage ) ; 7 ; $$AbstandTage ) ]
Wenn [ $anzahl < 1 ]
    Aktuelles Skript verlassen [ ]
Ende (wenn)
Wenn [ IstLeer ( Termine::Serie_ID ) ]
    Feldwert setzen [ Termine::Serie_ID ; Hole ( UUID ) ]
Ende (wenn)
Variable setzen [ $i ; Wert: 0 ]
Schleife (Anfang)
    Variable setzen [ $i ; Wert: $i + 1 ]
    Verlasse Schleife wenn [ $i > $anzahl ]
    Datensatz/Abfrage duplizieren
    Feldwert setzen [ Termine::Beginn ; Termine::Beginn + $abstand * 86400 ]
    Feldwert setzen [ Termine::Ende ; Termine::Ende + $abstand * 86400 ]
    Feldwert setzen [ Termine::Google_Event_ID ; "" ]
    Datensatz/Abfrage übernehmen [ Ohne Dialog ]
Schleife (Ende)
```

Die Schleife endet immer, auch bei leeren oder negativen Eingaben. Weil jedes Duplikat vom
vorherigen ausgeht, entsteht die Reihe 1×, 2×, 3× Abstand. Zeitstempel rechnen in Sekunden,
daher `* 86400` für Tage.

## 7. Google-Kalender-Abgleich (Vorschau, folgt als eigenes Dokument)

- Der Abgleich läuft per **„Aus URL einfügen“** mit cURL-Optionen gegen die Google Calendar API.
  Verbindungen gehen nur **vom Hof nach außen**.
- **Anfragen holen:** Neue Einträge aus dem Google-Kalender „Anfragen“ als Termine mit
  `Status = angefragt`, `Quelle = Google` anlegen, danach bei Google löschen (Datenschutz).
- **Belegung senden:** Bei Freigabe den Termin in den Google-Kalender „Belegung“ schreiben, nur Raum
  und „belegt“ oder Titel, ohne Kontaktdaten. Die Antwort enthält die Event-ID, sie wird in
  `Google_Event_ID` gespeichert. Bei Änderung oder Storno wird über diese ID aktualisiert oder gelöscht.
- Ohne FileMaker Server wird der Abgleich per Taste oder beim Öffnen der Datei gestartet. Mit Server
  läuft er später als geplantes Skript im Hintergrund.

## 8. Reihenfolge für den Umbau

Vor jedem Schritt: **Sicherungskopie** der Datei anlegen (Datei → Kopie speichern unter).

1. Werteliste „Status“ und „Art“ anlegen. Raumnamen festlegen.
2. In `A_Veranstaltungsräume` die Felder Aktiv, Sortierung, Kapazität ergänzen.
3. Neue Tabelle **Termine** anlegen (Abschnitt 3), Beziehungen zu Räume und Adressen setzen.
4. Daten aus den drei bisherigen Terminkalendern in **Termine** importieren
   (Datei → Datensätze importieren). Dabei Raum- und Personennamen in IDs umsetzen.
   Dafür schreibe ich Ihnen auf Wunsch ein Hilfsskript.
5. Selbstbeziehung **Termine_Konflikt** anlegen, Felder `Raum_ID_bestätigt` und `Konflikt_Anzahl`.
6. Skripte „Termin freigeben“, „Termin ablehnen“, „Termin prüfen“ und Layout „Anfragen“ anlegen.
7. Veranstaltungsplanung mit `Termin_ID` an Termine koppeln. Tabelle **Einsätze** anlegen und
   die Helfer aus den Wiederholfeldern übertragen.
8. Defekte Skripte und Layouts aus Abschnitt 2 entfernen, alte Tabellen erst löschen, wenn alles
   geprüft ist.
9. Google-Abgleich einrichten.
