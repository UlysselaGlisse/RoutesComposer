<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="de" sourcelanguage="fr">
<context>
    <name>ErrorDialog</name>
    <message>
        <location filename="../ui/sub_dialog.py" line="100"/>
        <source>Erreurs détectées</source>
        <translation>Erkannte Fehler</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="109"/>
        <source>Détails des erreurs détectées :</source>
        <translation>Fehlerdetails:</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="122"/>
        <source>Fermer</source>
        <translation>Schließen</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="165"/>
        <source>Les géométries pour les compositions suivantes n&apos;ont pas pu être créées : {composition_id}.</source>
        <translation>Die Geometrien für die folgenden Kompositionen konnten nicht erstellt werden: {composition_id}.</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="202"/>
        <source>Erreur</source>
        <translation>Fehler</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="202"/>
        <source>Segment {segment_id} non trouvé.</source>
        <translation>Segment {segment_id} nicht gefunden.</translation>
    </message>
</context>
<context>
    <name>InfoDialog</name>
    <message>
        <location filename="../ui/sub_dialog.py" line="31"/>
        <source>Informations sur le Gestionnaire de réseaux</source>
        <translation>Informationen zum Straßenkomponisten.</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="33"/>
        <source>
        &lt;b&gt;Gestionnaire de réseaux&lt;/b&gt;&lt;br&gt;&lt;br&gt;
        Ce plugin apporte une assistance dans la réalisation de réseaux en mettant &lt;br /&gt; à jour
        les compositions de segments en fonction des modifications &lt;br /&gt; faites sur les segments.&lt;br&gt;&lt;br&gt;
        &lt;i&gt;Instructions :&lt;/i&gt;&lt;br&gt;
        &lt;ol&gt;
            &lt;li&gt;Sélectionnez les couches à utiliser &lt;br /&gt; (La couche des compositions doit avoir
                un champ nommé &quot;segments&quot;)&lt;/li&gt;
            &lt;li&gt;Cliquez sur &apos;Démarrer&apos; pour activer le suivi&lt;/li&gt;
            &lt;li&gt;Effectuez vos modifications sur les segments&lt;/li&gt;
            &lt;li&gt;Les compositions seront mises à jour automatiquement&lt;/li&gt;
            &lt;li&gt;Cliquez sur &apos;Arrêter&apos; pour désactiver le suivi&lt;/li&gt;
        &lt;/ol&gt;

        Vous pouvez voir en détail ce qu&apos;il se passe en activant les logs &lt;br /&gt;
        Ceux-ci apparaîtront dans la console python de Qgis.
        </source>
        <translation type="obsolete">
&lt;b&gt;Netzwerkmanager&lt;/b&gt;&lt;br&gt;&lt;br&gt;
Dieses Plugin bietet Unterstützung beim Erstellen von Netzwerken, indem es&lt;br /&gt;
die Zusammensetzungen der Segmente basierend auf den Änderungen an den Segmenten aktualisiert.&lt;br&gt;&lt;br&gt;
&lt;i&gt;Anleitungen:&lt;/i&gt;&lt;br&gt;
&lt;ol&gt;
    &lt;li&gt;Wählen Sie die zu verwendenden Ebenen aus&lt;br /&gt;
        (Die Zusammensetzungsebene muss ein Feld namens &quot;segments&quot; haben)&lt;/li&gt;
    &lt;li&gt;Klicken Sie auf &apos;Start&apos;, um die Verfolgung zu aktivieren&lt;/li&gt;
    &lt;li&gt;Führen Sie Ihre Änderungen an den Segmenten durch&lt;/li&gt;
    &lt;li&gt;Die Zusammensetzungen werden automatisch aktualisiert&lt;/li&gt;
    &lt;li&gt;Klicken Sie auf &apos;Stop&apos;, um die Verfolgung zu deaktivieren&lt;/li&gt;
&lt;/ol&gt;

Sie können im Detail sehen, was passiert, indem Sie die Protokolle aktivieren&lt;br /&gt;
Diese erscheinen in der Python-Konsole von QGIS.</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="74"/>
        <source>Désactiver le logging</source>
        <translation type="obsolete">Logging deaktivieren</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="76"/>
        <source>Activer le logging</source>
        <translation type="obsolete">Enable logging</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="33"/>
        <source>
        &lt;b&gt;Gestionnaire de compositions de segments&lt;/b&gt;&lt;br&gt;&lt;br&gt;
        Ce plugin apporte une assistance dans la réalisation de compositions de segments.&lt;br&gt;&lt;br&gt;
        &lt;i&gt;Instructions :&lt;/i&gt;&lt;br&gt;
        &lt;ol&gt;
            &lt;li&gt;&lt;b&gt;Sélectionnez les couches :&lt;/b&gt;&lt;br /&gt;
                - Une couche segments avec un champ &apos;id&apos; qui sera utilisé pour faire vos compositions.&lt;br /&gt;
                - Une couche compositions avec un champ dans lequel vous entrez les listes de segments (sans espaces et séparées par une virgule, par exemple 1,2,3).&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Panier à segments :&lt;/b&gt;&lt;br /&gt;
                Cliquez sur l&apos;icône, une petite bulle apparaîtra à droite du curseur. Sélectionnez les segments qui vous intéressent. La liste se remplira.&lt;br /&gt;
                L&apos;outil cherchera toujours à combler les trous entre deux segments.&lt;br /&gt;
                Vous pouvez appuyer sur &lt;b&gt;z&lt;/b&gt; pour retirer le dernier segment ajouté à la liste et sur &lt;b&gt;e&lt;/b&gt; pour le rétablir.&lt;/li&gt;
        &lt;/ol&gt;
        </source>
        <translation>        &lt;b&gt;Segmentkompositionsmanager&lt;/b&gt;&lt;br&gt;&lt;br&gt;
        Dieses Plugin bietet Unterstützung bei der Erstellung von Segmentkompositionen.&lt;br&gt;&lt;br&gt;
        &lt;i&gt;Anweisungen:&lt;/i&gt;&lt;br&gt;
        &lt;ol&gt;
            &lt;li&gt;&lt;b&gt;Wählen Sie die Ebenen aus:&lt;/b&gt;&lt;br /&gt;
                - Eine Segmenteebene mit einem &apos;id&apos;-Feld, das für Ihre Kompositionen verwendet wird.&lt;br /&gt;
                - Eine Kompositionsebene mit einem Feld, in das Sie die Listen der Segmente eingeben (ohne Leerzeichen und durch Kommas getrennt, z.B. 1,2,3).&lt;/li&gt;
            &lt;li&gt;&lt;b&gt;Segmentkorb:&lt;/b&gt;&lt;br /&gt;
                Klicken Sie auf das Symbol, eine kleine Blase erscheint rechts vom Cursor. Wählen Sie die Segmente von Interesse aus. Die Liste füllt sich.&lt;br /&gt;
                Das Werkzeug versucht immer, Lücken zwischen zwei Segmenten zu füllen.&lt;br /&gt;
                Sie können &lt;b&gt;z&lt;/b&gt; drücken, um das zuletzt hinzugefügte Segment aus der Liste zu entfernen, und &lt;b&gt;e&lt;/b&gt;, um es wiederherzustellen.&lt;/li&gt;
        &lt;/ol&gt;
</translation>
    </message>
</context>
<context>
    <name>RoutesComposer</name>
    <message>
        <location filename="../main.py" line="178"/>
        <source>Le champ &apos;id&apos; n&apos;a pas été trouvé dans la couche segments</source>
        <translation>Das Feld &apos;id&apos; wurde in der Schicht Segmente nicht gefunden</translation>
    </message>
    <message>
        <location filename="../main.py" line="70"/>
        <source>Le suivi par RoutesComposer a démarré</source>
        <translation>Die Überwachung durch RoutesComposer hat begonnen</translation>
    </message>
    <message>
        <location filename="../main.py" line="100"/>
        <source>Erreur</source>
        <translation>Fehler</translation>
    </message>
    <message>
        <location filename="../main.py" line="92"/>
        <source>Le suivi par RoutesComposer est arrêté</source>
        <translation>Die Überwachung durch RoutesComposer ist gestoppt</translation>
    </message>
    <message>
        <location filename="../main.py" line="42"/>
        <source>Aucun projet QGIS n&apos;est ouvert</source>
        <translation>Kein QGIS-Projekt ist geöffnet</translation>
    </message>
    <message>
        <location filename="../main.py" line="147"/>
        <source>Veuillez sélectionner une couche de segments valide</source>
        <translation>Bitte wählen Sie eine gültige Segmentebene aus</translation>
    </message>
    <message>
        <location filename="../main.py" line="150"/>
        <source>La couche de segments n&apos;est pas une couche vectorielle valide</source>
        <translation>Die Segmentebene ist keine gültige Vektorebene</translation>
    </message>
    <message>
        <location filename="../main.py" line="160"/>
        <source>Veuillez sélectionner une couche de compositions valide</source>
        <translation>Bitte wählen Sie eine gültige Kompositionsschicht aus</translation>
    </message>
    <message>
        <location filename="../main.py" line="162"/>
        <source>La couche de compositions n&apos;est pas une couche vectorielle valide</source>
        <translation>Die Kompositionsschicht ist keine gültige Vektorschicht</translation>
    </message>
</context>
<context>
    <name>RoutesComposerDialog</name>
    <message>
        <location filename="../main.py" line="193"/>
        <source>Gestionnaire de réseaux</source>
        <translation type="obsolete">Netzwerk-Manager</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="89"/>
        <source>Configuration des couches</source>
        <translation>Layer-Konfiguration</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="93"/>
        <source>Couche segments:</source>
        <translation>Segments Layer:</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="105"/>
        <source>Couche compositions:</source>
        <translation>Kompositions Layer:</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="124"/>
        <source>Configuration de la liste de segments</source>
        <translation>Konfiguration der Segmentliste</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="128"/>
        <source>Colonne contenant la liste de segments:</source>
        <translation>Spalte mit der Liste der Segmente:</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="264"/>
        <source>Status: Arrêté</source>
        <translation>Status: Gestoppt</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="153"/>
        <source>Info</source>
        <translation>Info</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="160"/>
        <source>Démarrer automatiquement au lancement du projet</source>
        <translation>Automatisch beim Start des Projekts starten</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="461"/>
        <source>Attention</source>
        <translation>Achtung</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="461"/>
        <source>Veuillez sélectionner les couches segments et compositions</source>
        <translation>Bitte wählen Sie die Schichten Segmente und Kompositionen aus</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="237"/>
        <source>Veuillez sélectionner la colonne segments</source>
        <translation>Bitte wählen Sie die Spalte Segmente aus</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="469"/>
        <source>Erreur</source>
        <translation>Fehler</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="254"/>
        <source>Une erreur est survenue: {str(e)}</source>
        <translation>Ein Fehler ist aufgetreten: {str(e)}</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="259"/>
        <source>Arrêter</source>
        <translation>Stoppen</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="260"/>
        <source>Status: En cours d&apos;exécution</source>
        <translation>Status: In Ausführung</translation>
    </message>
    <message>
        <location filename="../main.py" line="460"/>
        <source>
        Gestionnaire de réseaux

        Ce plugin apporte une assistance dans
        la réalisation de réseaux en mettant à jour
        les compositions de segments en fonction
        des modifications faites sur les segments.

        Instructions :
        1. Sélectionnez les couches à utiliser
            (La couche des compositions doit avoir
            un champ nommé &quot;segments&quot;)
        2. Cliquez sur &apos;Démarrer&apos; pour activer le suivi
        3. Effectuez vos modifications sur les segments
        4. Les compositions seront mises à jour automatiquement
        5. Cliquez sur &apos;Arrêter&apos; pour désactiver le suivi
        </source>
        <translation type="obsolete">
        Netzwerk-Manager

        Dieses Plugin bietet Unterstützung bei der Erstellung von Netzwerken, indem es die Zusammensetzungen der Segmente basierend auf den Änderungen an den Segmenten aktualisiert.

        Anweisungen:
        1. Wählen Sie die zu verwendenden Ebenen aus
        (Die Ebene der Zusammensetzungen muss ein Feld namens &quot;Segmente&quot; haben)
        2. Klicken Sie auf &apos;Starten&apos;, um die Überwachung zu aktivieren
        3. Nehmen Sie Ihre Änderungen an den Segmenten vor
        4. Die Zusammensetzungen werden automatisch aktualisiert
        5. Klicken Sie auf &apos;Stoppen&apos;, um die Überwachung zu deaktivierenNetzwerk-Manager**
</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="52"/>
        <source>Compositeur de Routes</source>
        <translation>Routenkomponist</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="110"/>
        <source>Activer la création géométrique en continue</source>
        <translation>Aktivieren Sie die kontinuierliche geometrische Erstellung.</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="263"/>
        <source>Démarrer</source>
        <translation>Start</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="171"/>
        <source>Vérifier les compositions</source>
        <translation>Kompositionen überprüfen</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="332"/>
        <source>Créer les géométries</source>
        <translation>Geometrien erstellen</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="184"/>
        <source>Annuler</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="314"/>
        <source>Attention: la couche des segments n&apos;a pas de géométrie</source>
        <translation>Achtung: Die Segmentebene hat keine Geometrie</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="327"/>
        <source>Mettre à jour les géométries</source>
        <translation>Geometrien aktualisieren</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="358"/>
        <source>Attention: la colonne segments n&apos;est pas de type texte</source>
        <translation>Achtung: Die Spalte Segmente ist nicht vom Typ Text</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="415"/>
        <source>Aucune erreur</source>
        <translation>Keine Fehler</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="415"/>
        <source>Aucune erreur détectée.</source>
        <translation>Keine Fehler erkannt.</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="428"/>
        <source>Le champ {ss} n&apos;existe pas dans la couche des compositions.</source>
        <translation>Das Feld {ss} existiert nicht in der Kompositionsschicht.</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="469"/>
        <source>Le champ {segments_column_name} n&apos;existe pas dans la couche des compositions.</source>
        <translation>Das Feld {ss} existiert nicht in der Kompositionsschicht.</translation>
    </message>
    <message>
        <location filename="../ui/main_dialog.py" line="500"/>
        <source>Annulation en cours...</source>
        <translation>Stornierung läuft...</translation>
    </message>
</context>
<context>
    <name>RoutesComposerTool</name>
    <message>
        <location filename="../ui/tool.py" line="48"/>
        <source>Ouvrir Routes Composer</source>
        <translation type="obsolete">Route Komponist öffnen</translation>
    </message>
</context>
<context>
    <name>RoutesManagerTool</name>
    <message>
        <location filename="../ui/tool.py" line="58"/>
        <source>Ouvrir le panier à segments</source>
        <translation>Öffnen Sie den Segmentkorb</translation>
    </message>
</context>
<context>
    <name>SingleSegmentDialog</name>
    <message>
        <location filename="../ui/sub_dialog.py" line="55"/>
        <source>Vérification nécessaire</source>
        <translation>Überprüfung erforderlich</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="63"/>
        <source>Attention, composition d&apos;un seul segment. Veuillez vérifier que la nouvelle composition est bonne.</source>
        <translation>Achtung, Komposition aus einem einzigen Segment. Bitte überprüfen Sie, ob die neue Komposition korrekt ist.</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="74"/>
        <source>Inverser l&apos;ordre</source>
        <translation>Die Reihenfolge umkehren</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="82"/>
        <source>Annuler</source>
        <translation>Abbrechen</translation>
    </message>
    <message>
        <location filename="../ui/sub_dialog.py" line="90"/>
        <source>Nouvelle composition proposée: {cs}</source>
        <translation>Neuer vorgeschlagener Komposition: {cs}</translation>
    </message>
</context>
</TS>
