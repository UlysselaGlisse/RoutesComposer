This README is also available in [:gb: English](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-en.md) and [:de: German](https://github.com/UlysselaGlisse/RoutesComposer/blob/main/i18n/README-de.md)

This QGIS plugin will be useful for those who want to create routes between two points from a vector network. The most obvious example of a network is that of roads: the D42 road is both a single road and is made up of dozens of different sections.
The sections are in the plugin the segments, and the road corresponds to a composition.
All geographical work is done on the segments. The compositions only have attributes and a list containing the identifiers of the segments.

## Division

The first function of this plugin is to assist during the division of a segment. If the segment is part of one or more compositions, it can be tedious to find out which ones and where. The plugin takes care of this for you.

![Segment Division](https://github.com/user-attachments/assets/82e68484-61c9-49c2-8f8e-dd5668f01f40)

In the video above, you can see a set of segments on the map and a list of segments at the bottom of the screen. When segment 2516 is divided, a new segment is created, and the lists of segments are automatically updated.

## Creating Geometries and Errors:

You will be able to directly create the geometries of the compositions from the plugin interface, update them if your layer already has them, and refresh them each time a segment's geometry is modified.

![RoutesComposer](https://github.com/user-attachments/assets/33897f19-8f54-49e9-b7ea-8a9dd685000d)

## Selection

This plugin comes with another tool that allows you to select segment IDs directly on the map. A small algorithm helps fill in gaps if you do not select two contiguous segments.

![Selection Tool](https://github.com/user-attachments/assets/e7506320-665e-49fe-bef8-5ba32d06b17d)

---

# Installation

Download this repository:

```bash
git clone https://github.com/UlysselaGlisse/RoutesComposer.git
```

* Linux:

Move the directory to the QGIS plugins folder, usually located at:

`~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

* Windows:

`C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`

* Mac OS:

`Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

---

In QGIS, go to Plugins > Manage and Install Plugins.

Type "RoutesComposer" - if it does not appear, restart QGIS - > Check the checkbox.

# Usage
### Prerequisites:
* Two input layers are required, one for the segments and another for the compositions.
* The layers can be in any format (GeoPackage, PostgreSQL, shapefile, GeoJSON, ...).
* They can be named as you wish.
* The only requirement is that the field containing the list of segments must be of type string, and the segments layer must have a field named "id" - the one you use to build your compositions.

### Uses:
#### Route Composer
* Click on the icon ![icon](ui/icons/icon.png)
* Enter the names of the two layers and the field of the compositions layer that contains the list of segments.
* Start the process.
* You may also choose to let this plugin run continuously by checking the corresponding box.

#### Segment Basket
* Click on the icon ![icon](ui/icons/ids_basket.png)
* A small box will appear next to the cursor.
* Click on the segments that interest you. The box fills up.
* If you wish to remove the last added segment, press Z; press E to add it back.
* To empty the box, right-click.
* The segments are copied to the clipboard with each addition. You can then paste them where needed.

# Trial
If you simply want to try this plugin, you will find an example GeoPackage in the etc/ folder. Open it and give it a try.
