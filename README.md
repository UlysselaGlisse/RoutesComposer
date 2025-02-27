# RoutesComposer

This README is also available in [:fr: French](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-fr.md) and [:de: German](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-de.md)

This QGIS plugin allows you to create routes between two points from a vector network. The most obvious example of a network is that of roads: department road 42 is both a single road and consists of dozens of different sections.

The sections are segments in the plugin, while the department road corresponds to a composition. All geographical work is done on the segments. Compositions only have attributes and a list containing the identifiers of the segments.

## Division

The first function of this plugin is to assist when dividing a segment. If the segment is part of one or more compositions, it can be cumbersome to find in which ones and at what location. The plugin takes care of this for you.

https://github.com/user-attachments/assets/82e68484-61c9-49c2-8f8e-dd5668f01f40

In the video above, you can see a set of segments on the map and a list of segments at the bottom of the screen. When segment 2516 is divided, a new segment is created, and the lists of segments are automatically updated.

## Creating Geometries and Check Errors:

You will be able to directly create the geometries of compositions from the plugin interface, update them if your layer already has them, and refresh them with each modification of the segment geometries.


![Main_dialog](https://github.com/user-attachments/assets/82146abb-d07f-45f1-a74f-90a00c19ee88)

## Selection

This plugin is accompanied by another tool that allows you to select the IDs of segments directly on the map. A small algorithm fills in the gaps if two contiguous segments are not selected.

[panier_a_segments.webm](https://github.com/user-attachments/assets/4d1505bb-728e-4c06-a9ee-7f2c874a5062)

# Installation

Go to the plugin extension menu of Qgis and search for RoutesComposer.

---

# Usage
### Prerequisites:
* Two input layers are required, one for segments and another for compositions.
* The layers can be in any format (GeoPackage, PostgreSQL, geojson, ...).
* They can have any name you want.
* The only requirement is that the field containing the segment list must be of type string, and the segment layer must have a field named "id" - the one used to build your compositions - and a unique feature id (fid).

### Uses:
#### Route Composer
* Click on the icon ![icon](ui/icons/icon.png).
* Enter the names of the two layers and the field of the composition layer where the list of segments is located.
* Start.
* You may also choose to have this plugin run continuously by checking the corresponding box.

#### Segment Basket
* Click on the icon ![icon](ui/icons/ids_basket.png).
* Click on the segments you are interested in. The box will fill up.
* If you want to remove the last added segment, press Z, E to restore it.
* When you have all the segments desired, right-click, the attribute form will open with the segments attribute column fill up.

#### Geometries of compositions
* When you want to export you'r work, you can open the RoutesComposer's dialog and click on Create Geometries. That will create a new layer with the geometries of all the compositions.
* If you want to work next with a compositions layer with geometries, you can erase you'r old compositions layer with the new one by save the new layer at the path of the old one.
* You can now click in the dialog on Allow geometry creation on the fly, and every time that a geometry of segments layer is changed, the compositions one will be changed.

# Trial
If you simply want to try this plugin, you will find an example GeoPackage in the etc/ folder. Open it and give it a try.
