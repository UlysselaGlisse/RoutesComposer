# RoutesComposer

This README is also available in [:gb: English](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-en.md) and [:de: German](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-de.md)

This QGIS plugin allows you to create routes between two points from a vector network. The most obvious example of a network is that of roads: department road 42 is both a single road and consists of dozens of different sections.

The sections are segments in the plugin, while the department road corresponds to a composition. All geographical work is done on the segments. Compositions only have attributes and a list containing the identifiers of the segments.

## Division

The first function of this plugin is to assist when dividing a segment. If the segment is part of one or more compositions, it can be cumbersome to find in which ones and at what location. The plugin takes care of this for you.

https://github.com/user-attachments/assets/82e68484-61c9-49c2-8f8e-dd5668f01f40

In the video above, you can see a set of segments on the map and a list of segments at the bottom of the screen. When segment 2516 is divided, a new segment is created, and the lists of segments are automatically updated.

## Creating Geometries and Errors:

You will be able to directly create the geometries of compositions from the plugin interface, update them if your layer already has them, and refresh them with each modification of the segment geometries.

![RoutesComposer](https://github.com/user-attachments/assets/33897f19-8f54-49e9-b7ea-8a9dd685000d)

## Selection

This plugin is accompanied by another tool that allows you to select the IDs of segments directly on the map. A small algorithm fills in the gaps if two contiguous segments are not selected.

https://github.com/user-attachments/assets/e7506320-665e-49fe-bef8-5ba32d06b17d

# Installation

* Download this [file](https://github.com/UlysselaGlisse/RoutesComposer/releases/download/v1.1/RoutesComposer.zip).
* In QGIS > Plugins > Install from ZIP.
* Choose the zipped file.
* Install the Plugin.

*If the plugin does not appear, go to Plugins > Installed > Check the plugin icon.*

---

# Usage
### Prerequisites:
* Two input layers are required, one for segments and another for compositions.
* The layers can be in any format (GeoPackage, PostgreSQL, shp, geojson, ...).
* They can have any name you want.
* The only requirement is that the field containing the segment list must be of type string, and the segment layer must have a field named "id" - the one used to build your compositions.

### Uses:
#### Route Composer
* Click on the icon ![icon](ui/icons/icon.png).
* Enter the names of the two layers and the field of the composition layer where the list of segments is located.
* Start.
* You may also choose to have this plugin run continuously by checking the corresponding box.

#### Segment Basket
* Click on the icon ![icon](ui/icons/ids_basket.png).
* A small box will appear next to the cursor.
* Click on the segments you are interested in. The box will fill up.
* If you want to remove the last added segment, press Z, E to restore it.
* To empty the box, right-click.
* Segments are copied to the clipboard with each addition. You just have to paste them where needed.

# Trial
If you simply want to try this plugin, you will find an example GeoPackage in the etc/ folder. Open it and give it a try.
