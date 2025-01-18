from qgis.PyQt.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
)


class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Informations sur Routes Composer"))
        self.resize(400, self.height())

        info_text = self.tr(
            """
            <!DOCTYPE html>
                <h2>Gestionnaire de compositions de segments</h2>
                <p>Ce plugin apporte une assistance dans la réalisation de compositions de segments.</p>

                <p><i>Instructions :</i></p>

                <h4>Sélectionnez les couches :</h4>
                <p>
                Les couches sélectionnées ne peuvent avoir pour identifiant unique la colonne 'id'<br>
                choisie pour routes composer. Pour un gpkg, il faudra typiquement avoir une colonne 'fid'<br>
                et une colonne 'id'.<br>
                <br>
                    - Une couche segments avec un champ 'id' qui sera utilisé pour faire vos compositions.<br>
                    - Une couche compositions avec un champ dans lequel vous entrez les listes de segments<br> (sans espaces et séparées par une virgule, par exemple 1,2,3).
                </p>

                <h4>Panier à segments :</h4>
                <p>
                    - Cliquez sur l'icône du panier.<br>
                    - Sélectionnez les segments qui vous intéressent. La liste se remplira.<br>
                    L'outil cherchera toujours à combler les trous entre deux segments. <br>
                    - Clique-droit. Le formulaire d'ajout d'une entité s'ouvre.
                </p>

                <h4>Raccourcis:</h4>
                <ul>
                    - <b>z</b> pour retirer le dernier segment de la liste<br>
                    - <b>r</b> pour le rétablir<br>
                    - <b>e</b> pour vider la liste<br>
                    - <b>alt + clique-gauche</b> pour sélectionner tous les segments d'une composition<br>
                    - <b>shift + clique-droit</b> pour copier la sélection dans le presse papier<br>
                </ul>
            </div>
            """
        )

        layout = QVBoxLayout()
        layout.addWidget(QLabel(info_text))
        self.setLayout(layout)
