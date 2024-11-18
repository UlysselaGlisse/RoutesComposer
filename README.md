THis README is also available in [:gb: English](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-en.md) and [:de: German](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-de.md)



Ce plugin Qgis sera utile à ceux qui souhaitent créer des routes entre deux points à partir d'un réseau de vecteurs (de lignes).
L'exemple le plus évident de réseau est celui des routes :
la départementale 42 est à la fois une seule route et est composée de dizaines de sections différentes.

Les sections sont dans le plugin des segments, et la départementale correspond à une composition.

Tout le travail géographique s'effectue sur les segments. Les compositions ne possèdent que des attributs et une liste avec les identifiants des segments.

## Division

La première fonction de ce plugin est d'aider au moment de la division d'un segment.
Si le segment fait partie d'une ou plusieurs compositions, il est pénible d'aller chercher dans lesquelles et à quel endroit.
Le plugin s'occupe de cela à votre place.

https://github.com/user-attachments/assets/82e68484-61c9-49c2-8f8e-dd5668f01f40

Dans la vidéo ci-dessus, vous pouvez voir un ensemble de segments sur la carte et une liste de segments en bas de l'écran. Lorsque le segment 2516 est divisé, un nouveau segment est créé et les listes de segments sont automatiquement mises-à-jour.

## Création de géométries et erreurs:

Vous pourrez directement depuis l'interface du plugin créer les géométries des compositions, les mettre à jour si votre couche en possède déjà et les mettre à jour à chaque modification de la géométrie des segments.

![RoutesComposer](https://github.com/user-attachments/assets/33897f19-8f54-49e9-b7ea-8a9dd685000d)


## Sélection

Ce plugin est accompagné d'un autre outil, permettant de sélectionner les ids des segments directement sur la carte. Un petit algorithme permet de boucher les trous si l'on ne sélectionne pas deux segments contigus.

https://github.com/user-attachments/assets/e7506320-665e-49fe-bef8-5ba32d06b17d







# Installation

* Télécharger ce (fichier)[https://github.com/UlysselaGlisse/RoutesComposer/releases/download/v1.0/RoutesComposer.zip]
* Dans Qgis > Extensions > Installer depuis un ZIP
* Choisir le fichier zippé.
* Installer le Plugin.

_Si jamais le plugin n'apparaît pas, se rendre dans Extensions > Installées > Cocher l'icone du plugin._
---


Dans Qgis, Extensions >  Installer/Gérer les extensions

Taper RoutesComposer - s'il n'apparaît pas, redémarrer Qgis - > Cocher la checkbox.

# Utilisation
### Prérequis:
* Deux couches sont requises en entrée, une pour les segments et une autre pour les compositions.
* Les couches peuvent être de n'importe quel format (GeoPackage, Postgresql, shp, geojson, ...).
* Elles peuvent avoir le nom que vous souhaitez
* La seule chose nécessaire est que le champ contenant la liste de segments soit de type string et que la couche des segments ait un champ nommé "id" - celui avec lequel vous construisez vos compositions.

### Usages:
#### Compositeur de routes
* Cliquer sur l'icone ![icône](ui/icons/icon.png)
* Entrer le nom des deux couches puis du champ de la couche des compositions où se trouve la liste des segments.
* Démarrer
* Vous pouvez aussi choisir de laisser tourner ce plugin en permanence en cochant la case correspondante.


#### Panier à segments

* Cliquer sur l'icone ![icône](ui/icons/ids_basket.png)
* Vous verrez apparaître une petite boîte à côté du curseur.
* Cliquez sur les segments qui vous intéressent. La boîte se remplie.
* Si vous souhaitez retirer le dernier segment ajouté, appuyez sur Z, E pour le remettre.
* Pour vider la boite, faites un clique-droit
* Les segments sont copiés dans le presse-papier à chaque ajout. Vous n'avez qu'à les coller là où il le faut.



# Essai
Si vous souhaitez simplement essayer ce plugin, vous trouverez dans le dossier etc/ un Géopackage d'exemple.
Ouvrez-le et essayez.
