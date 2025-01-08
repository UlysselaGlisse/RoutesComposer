from qgis.PyQt.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
)


class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Informations sur le Gestionnaire de réseaux"))

        info_text = self.tr(
            """
        <b>Gestionnaire de compositions de segments</b><br><br>
        Ce plugin apporte une assistance dans la réalisation de compositions de segments.<br><br>
        <i>Instructions :</i><br>
        <ol>
            <b>Sélectionnez les couches :</b><br />
                - Une couche segments avec un champ 'id' qui sera utilisé pour faire vos compositions.<br />
                - Une couche compositions avec un champ dans lequel vous entrez les listes de segments (sans espaces et séparées par une virgule, par exemple 1,2,3).<br /><br />
            <b>Panier à segments :</b><br />
                Cliquez sur l'icône, une petite bulle apparaîtra à droite du curseur. Sélectionnez les segments qui vous intéressent. La liste se remplira.<br />
                L'outil cherchera toujours à combler les trous entre deux segments.<br />
                Vous pouvez appuyer sur <b>z</b> pour retirer le dernier segment ajouté à la liste et sur <b>e</b> pour le rétablir.</li>
        </ol>
        """
        )

        layout = QVBoxLayout()
        layout.addWidget(QLabel(info_text))
        self.setLayout(layout)
