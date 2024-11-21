Dieses README ist auch verfügbar in [:gb: Englisch](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-en.md) und [:de: Deutsch](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-de.md)

Dieses QGIS-Plugin ist hilfreich für diejenigen, die Routen zwischen zwei Punkten aus einem Vektornetzwerk (Linien) erstellen möchten. Das naheliegendste Beispiel für ein Netzwerk sind Straßen: Die D42-Straße ist sowohl eine einzelne Straße als auch aus Dutzenden verschiedener Segmente zusammengesetzt.

Die Segmente sind die Bausteine des Plugins, und die Straße entspricht einer Komposition.

Alle geografischen Arbeiten werden an den Segmenten ausgeführt. Die Kompositionen haben nur Attribute und eine Liste mit den Identifikatoren der Segmente.

## Teilung

Die erste Funktion dieses Plugins besteht darin, bei der Teilung eines Segments zu helfen. Wenn das Segment Teil einer oder mehrerer Kompositionen ist, kann es mühsam sein, herauszufinden, in welchen und wo. Das Plugin übernimmt dies für Sie.

![Segmentteilung](https://github.com/user-attachments/assets/82e68484-61c9-49c2-8f8e-dd5668f01f40)

Im obigen Video sehen Sie eine Reihe von Segmenten auf der Karte und eine Segmentliste am unteren Bildschirmrand. Wenn das Segment 2516 geteilt wird, wird ein neues Segment erstellt, und die Listen der Segmente werden automatisch aktualisiert.

## Erstellen von Geometrien und Fehlern:

Sie können direkt über die Plugin-Oberfläche die Geometrien der Kompositionen erstellen, sie aktualisieren, wenn Ihre Ebene bereits welche hat, und sie bei jeder Änderung der Geometrie der Segmente aktualisieren.

![RoutesComposer](https://github.com/user-attachments/assets/33897f19-8f54-49e9-b7ea-8a9dd685000d)

## Auswahl

Dieses Plugin wird von einem anderen Tool begleitet, das es ermöglicht, die Segment-IDs direkt auf der Karte auszuwählen. Ein kleiner Algorithmus hilft dabei, Lücken zu schließen, wenn Sie nicht zwei zusammenhängende Segmente auswählen.

![Auswahlwerkzeug](https://github.com/user-attachments/assets/e7506320-665e-49fe-bef8-5ba32d06b17d)

---

# Installation

* Laden Sie diese [Datei](https://github.com/UlysselaGlisse/RoutesComposer/releases/download/v1.0/RoutesComposer.zip) herunter
* In QGIS > Plugins > Aus ZIP installieren
* Wählen Sie die gezippte Datei aus.
* Installieren Sie das Plugin.

_Wenn das Plugin nicht angezeigt wird, gehen Sie zu Plugins > Installiert > Aktivieren Sie das Symbol des Plugins._

---

In QGIS gehen Sie zu Plugins > Erweiterungen verwalten und installieren.

Geben Sie "RoutesComposer" ein – wenn es nicht angezeigt wird, starten Sie QGIS neu – > Aktivieren Sie das Kontrollkästchen.

# Verwendung
### Voraussetzungen:
* Zwei Eingabeschichten sind erforderlich, eine für die Segmente und eine andere für die Kompositionen.
* Die Schichten können in jedem Format vorliegen (GeoPackage, PostgreSQL, Shapefile, GeoJSON, ...).
* Sie können beliebig benannt werden.
* Die einzige Anforderung ist, dass das Feld, das die Liste der Segmente enthält, vom Typ String sein muss, und die Segmentebene muss ein Feld namens "id" enthalten – das, mit dem Sie Ihre Kompositionen erstellen.

### Anwendungen:
#### Routenkomponist
* Klicken Sie auf das Symbol ![Symbol](../ui/icons/icon.png)
* Geben Sie die Namen der beiden Schichten und das Feld der Kompositionsschicht ein, das die Liste der Segmente enthält.
* Starten Sie den Prozess.
* Sie können auch wählen, ob Sie dieses Plugin kontinuierlich ausführen möchten, indem Sie das entsprechende Kästchen aktivieren.

#### Segmentkorb
* Klicken Sie auf das Symbol ![Symbol](../ui/icons/ids_basket.png)
* Ein kleines Feld erscheint neben dem Cursor.
* Klicken Sie auf die Segmente, die Sie interessieren. Das Feld füllt sich.
* Wenn Sie das zuletzt hinzugefügte Segment entfernen möchten, drücken Sie Z; drücken Sie E, um es wieder hinzuzufügen.
* Um das Feld zu leeren, klicken Sie mit der rechten Maustaste.
* Die Segmente werden bei jeder Hinzufügung in die Zwischenablage kopiert. Sie können sie dann dort einfügen, wo sie benötigt werden.

# Test
Wenn Sie dieses Plugin einfach ausprobieren möchten, finden Sie im Ordner etc/ ein Beispiel-Geopackage. Öffnen Sie es und probieren Sie es aus.
