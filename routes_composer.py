from qgis.core import Qgis, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QObject, QSettings, QTranslator
from qgis.utils import iface
from typing_extensions import cast

from .func.attributes import AttributeLinker
from .func.geom_compo import GeomCompo
from .func.segments_belonging import SegmentsBelonging
from .func.split import SplitManager
from .func.utils import LayersAssociationManager, log, timer_decorator


class RoutesComposer(QObject):
    _instance = None

    @classmethod
    def get_instance(cls, parent=None):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = QgsProject.instance()
        if not self.project:
            return

        self.project.layersWillBeRemoved.connect(self.on_layer_removed)

        self.settings = QSettings()
        self.translator = QTranslator()

        self.segments_layer = self.get_segments_layer()
        self.compositions_layer = self.get_compositions_layer()
        self.segments_column_name, self.segments_column_index = (
            self.get_segments_column_name()
        )
        self.seg_id_column_name, self.id_column_index = self.get_id_column_name()

        self.lam = LayersAssociationManager(
            self.compositions_layer,
            self.segments_layer,
            self.segments_column_name,
            self.seg_id_column_name,
        )
        self.split = SplitManager(self)
        self.geom = GeomCompo(
            self.segments_layer,
            self.compositions_layer,
            self.seg_id_column_name,
            self.segments_column_name,
        )

        self.routes_composer_connected = False
        self.geom_on_fly_connected = False
        self.belonging_connected = False
        self.attribute_linker_connected = False

        self.seg_feature_added_connected = False
        self.seg_feature_deleted_connected = False
        self.seg_geom_changed_connected = False

        self.comp_feature_added_connected = False
        self.comp_feature_deleted_connected = False
        self.comp_attr_value_changed_connected = False

        self.is_splitting = False

    @timer_decorator
    def feature_added_on_segments(self, fid):
        """Traite l'ajout d'une nouvelle entité dans la couche segments."""
        # Pendant l'enregistrement: fid >= 0.'
        if fid >= 0:
            return
        if self.segments_layer is None or self.compositions_layer is None:
            return

        new_feature = self.segments_layer.getFeature(fid)

        if not new_feature.isValid():
            return

        segment_id = int(new_feature.attributes()[self.id_column_index])
        if segment_id is None:
            return

        next_id = self.split.get_next_id()

        if self.split.has_duplicate_segment_id(segment_id):
            new_geometry = new_feature.geometry()

            if not new_geometry or new_geometry.isEmpty():
                return

            original_feature = next(
                self.segments_layer.getFeatures(
                    f"{self.seg_id_column_name} = {segment_id}"
                ),
                None,
            )

            if original_feature:
                segments_lists_ids = self.lam.get_segments_list_for_segment(segment_id)

                # On ne peut pas enregistrer la couche avec commitChanges(), sûrement car c'est la couche appelée par le slot.'
                self.split.update_segment_id(fid, next_id)

                if segments_lists_ids:
                    self.split.update_compositions_segments(
                        fid,
                        segment_id,
                        next_id,
                        original_feature,
                        new_feature,
                        segments_lists_ids,
                    )
                    log(
                        f"Composition {[comp[0] for comp in segments_lists_ids]} has been updated. "
                        f"Segment {next_id} has been added in the lists."
                    )
                    if self.geom_on_fly_connected:
                        self.geom.update_geometries_on_the_fly(segment_id)

                    # self.compositions_layer.reload()

    def features_deleted_on_segments(self, fids):
        """
        Nettoie les compositions lorsqu'un segment est supprimé ou fusionné.
        """
        if self.segments_layer is None or self.compositions_layer is None:
            return

        self.split.clean_invalid_segments()
        log(f"Segments supprimées: {fids}")

    @timer_decorator
    def geometry_changed_on_segments(self, fid, idx, *args):
        """Crée la géométrie des compositions lors du changement de la géométrie d'un segment"""
        if self.segments_layer is None or self.compositions_layer is None:
            return

        source_feature = self.segments_layer.getFeature(fid)
        if not source_feature.isValid():
            return

        segment_id = source_feature.attributes()[self.id_column_index]
        if segment_id is None:
            return

        self.geom.update_geometries_on_the_fly(segment_id)
        self.compositions_layer.triggerRepaint()

    @timer_decorator
    def feature_added_on_compositions(self, fid):
        # On n'exécute pas ce qui suit lors de l'enregistrement.
        if fid >= 0:
            return

        if self.segments_layer is None or self.compositions_layer is None:
            return

        source_feature = self.compositions_layer.getFeature(fid)
        if not source_feature.isValid():
            return

        if not self.project:
            return
        compo_id_column_name, _ = (
            self.project.readEntry("routes_composer", "compo_id_column_name", "id")
            or "id"
        )

        log(
            f"New compositions feature added with id: {int(source_feature[compo_id_column_name])}"
        )

        if self.routes_composer_connected:
            segments_str = source_feature[self.segments_column_name]
            if not segments_str:
                return

            segments_list = [seg.strip() for seg in str(segments_str).split(",")]
            if not segments_list:
                return

            segment_id = int(segments_list[0])
            self.geom.update_geometries_on_the_fly(segment_id)
            self.compositions_layer.reload()

        if self.belonging_connected:
            self.belong = SegmentsBelonging(
                self.segments_layer,
                self.compositions_layer,
                self.seg_id_column_name,
                self.segments_column_name,
                compo_id_column_name=compo_id_column_name,
            )
            if self.belong.update_belonging_column(
                int(source_feature[compo_id_column_name])
            ):
                self.compositions_layer.commitChanges()
                log("Belonging column on segments layer updated.")

        saved_linkages = (
            self.settings.value("routes_composer/attribute_linkages", []) or []
        )
        if saved_linkages:
            attribute_linker = AttributeLinker(
                self.segments_layer,
                self.compositions_layer,
                self.seg_id_column_name,
                self.segments_column_name,
                saved_linkages,
            )
            if attribute_linker.update_segments_attr_values(
                int(source_feature[compo_id_column_name])
            ):
                self.compositions_layer.commitChanges()
                log("Attributes updated in segments layer")

        self.segments_layer.reload()

    @timer_decorator
    def feature_changed_on_compositions(self, fid, idx, *args):
        if self.segments_layer is None or self.compositions_layer is None:
            return

        source_feature = self.compositions_layer.getFeature(fid)
        if not source_feature.isValid():
            return

        if not self.project:
            return
        compo_id_column_name, _ = (
            self.project.readEntry("routes_composer", "compo_id_column_name", "id")
            or "id"
        )

        field_name = self.compositions_layer.fields()[idx].name()

        if field_name == self.segments_column_name and not self.is_splitting:
            if self.routes_composer_connected:
                segments_str = source_feature[self.segments_column_name]
                if not segments_str:
                    return

                segments_list = [seg.strip() for seg in str(segments_str).split(",")]
                if not segments_list:
                    return

                segment_id = int(segments_list[0])
                self.geom.update_geometries_on_the_fly(segment_id)
                self.compositions_layer.reload()

                log(
                    f"Geom of modified composition {source_feature[compo_id_column_name]} updated"
                )

            if self.belonging_connected and not self.is_splitting:
                self.belong = SegmentsBelonging(
                    self.segments_layer,
                    self.compositions_layer,
                    self.seg_id_column_name,
                    self.segments_column_name,
                    compo_id_column_name=compo_id_column_name,
                )
                if self.belong.update_belonging_column(
                    int(source_feature[compo_id_column_name])
                ):
                    self.compositions_layer.commitChanges()
                    log("Belonging column on segments layer updated.")

        settings = QSettings()
        saved_linkages = settings.value("routes_composer/attribute_linkages", []) or []

        if saved_linkages:
            for linkage in saved_linkages:
                if field_name == linkage["compositions_attr"]:
                    attribute_linker = AttributeLinker(
                        self.segments_layer,
                        self.compositions_layer,
                        self.seg_id_column_name,
                        self.segments_column_name,
                        saved_linkages if len(saved_linkages) > 1 else [linkage],
                    )
                    if attribute_linker.update_segments_attr_values(
                        int(source_feature[compo_id_column_name])
                    ):
                        log("Attributes updated in segments layer")

        self.segments_layer.reload()

    @timer_decorator
    def features_deleted_on_compositions(self, fids):
        if self.segments_layer is None or self.compositions_layer is None:
            return
        log(f"Features removed from compositions: {fids}")

        if not self.project:
            return
        compo_id_column_name, _ = (
            self.project.readEntry("routes_composer", "compo_id_column_name", "id")
            or "id"
        )

        if self.belonging_connected:
            self.belong = SegmentsBelonging(
                self.segments_layer,
                self.compositions_layer,
                self.seg_id_column_name,
                self.segments_column_name,
                compo_id_column_name,
            )
            if self.belong.update_belonging_column():
                log("Belonging column on segments layer updated.")

        settings = QSettings()
        saved_linkages = settings.value("routes_composer/attribute_linkages", []) or []

        if saved_linkages:
            attribute_linker = AttributeLinker(
                self.segments_layer,
                self.compositions_layer,
                self.seg_id_column_name,
                self.segments_column_name,
                saved_linkages,
            )
            if attribute_linker.update_segments_attr_values():
                log("Attributes updated in segments layer")

        self.segments_layer.reload()

    def connect_routes_composer(self):
        try:
            if self.segments_layer is not None and self.compositions_layer is not None:
                if not self.seg_feature_added_connected:
                    self.segments_layer.featureAdded.connect(
                        self.feature_added_on_segments
                    )
                    self.seg_feature_added_connected = True

                if not self.seg_feature_deleted_connected:
                    self.segments_layer.featuresDeleted.connect(
                        self.features_deleted_on_segments
                    )
                    self.seg_feature_deleted_connected = True

                # Geom on fly check :

                geom = self.project.readBoolEntry(
                    "routes_composer", "geom_on_fly", False
                )[0]
                if geom:
                    if not self.seg_geom_changed_connected:
                        self.segments_layer.geometryChanged.connect(
                            self.geometry_changed_on_segments
                        )
                        self.seg_geom_changed_connected = True

                    if not self.comp_feature_added_connected:
                        self.compositions_layer.featureAdded.connect(
                            self.feature_added_on_compositions
                        )
                        self.comp_feature_added_connected = True

                    if not self.comp_attr_value_changed_connected:
                        self.compositions_layer.attributeValueChanged.connect(
                            self.feature_changed_on_compositions
                        )
                        self.comp_attr_value_changed_connected = True

                    log("geom_on_fly connected" if geom else "")
                    self.geom_on_fly_connected = True

                # Appartenance des segments check :
                belonging = self.project.readBoolEntry("routes_composer", "belonging")[0]
                if belonging:
                    if not self.comp_feature_added_connected:
                        self.compositions_layer.featureAdded.connect(
                            self.feature_added_on_compositions
                        )
                        self.comp_feature_added_connected = True

                    if not self.comp_attr_value_changed_connected:
                        self.compositions_layer.attributeValueChanged.connect(
                            self.feature_changed_on_compositions
                        )
                        self.comp_attr_value_changed_connected = True

                    self.belonging_connected = True
                    log("Belonging connected" if belonging else "")
                self.routes_composer_connected = True

                log("Routes Composer has started", level="INFO")
                return True

        except Exception as e:
            iface.messageBar().pushMessage(
                self.tr("Erreur"),
                str(e),
                level=Qgis.MessageLevel.Critical,
            )
            return False

    def disconnect_routes_composer(self):
        if self.segments_layer is not None and self.compositions_layer is not None:
            # Déconnexion des signaux de la couche segments
            if self.seg_feature_added_connected:
                try:
                    self.segments_layer.featureAdded.disconnect(
                        self.feature_added_on_segments
                    )
                    self.seg_feature_added_connected = False
                except Exception as e:
                    log(
                        f"Erreur lors de la déconnexion de featureAdded on segments: {str(e)}"
                    )

            if self.seg_feature_deleted_connected:
                try:
                    self.segments_layer.featuresDeleted.disconnect(
                        self.features_deleted_on_segments
                    )
                    self.seg_feature_deleted_connected = False
                except Exception as e:
                    log(
                        f"Erreur lors de la déconnexion de featuresDeleted on segments: {str(e)}"
                    )

            if self.seg_geom_changed_connected:
                try:
                    self.segments_layer.geometryChanged.disconnect(
                        self.geometry_changed_on_segments
                    )
                    self.seg_geom_changed_connected = False
                except Exception as e:
                    log(
                        f"Erreur lors de la déconnexion de geometryChanged on segments: {str(e)}"
                    )

            # Déconnexion des signaux de la couche compositions
            if self.comp_feature_added_connected:
                try:
                    self.compositions_layer.featureAdded.disconnect(
                        self.feature_added_on_compositions
                    )
                    self.comp_feature_added_connected = False
                except Exception as e:
                    log(
                        f"Erreur lors de la déconnexion de featureAdded on compositions: {str(e)}"
                    )

            if self.comp_attr_value_changed_connected:
                try:
                    self.compositions_layer.attributeValueChanged.disconnect(
                        self.feature_changed_on_compositions
                    )
                    self.comp_attr_value_changed_connected = False
                except Exception as e:
                    log(
                        f"Erreur lors de la déconnexion de attributeValueChanged on compositions: {str(e)}"
                    )

            if self.comp_feature_deleted_connected:
                try:
                    self.compositions_layer.featureDeleted.disconnect(
                        self.features_deleted_on_compositions
                    )
                    self.comp_feature_deleted_connected = False
                except Exception as e:
                    log(
                        f"Erreur lors de la déconnexion de featureDeleted on compositions: {str(e)}"
                    )

            self.routes_composer_connected = False
            self.belonging_connected = False
            self.geom_on_fly_connected = False

            self.segments_layer = None
            self.compositions_layer = None
            self.seg_id_column_name = None
            self.comp_id_column_name = None
            self.id_column_index = None
            self.segments_column_index = None

            log("Script has been stopped.", level="INFO")

    def get_segments_layer(self):
        if not self.project:
            return

        self.segments_layer_id, _ = self.project.readEntry(
            "routes_composer", "segments_layer_id", ""
        )
        if not self.segments_layer_id:
            return
        self.segments_layer = cast(
            QgsVectorLayer, self.project.mapLayer(self.segments_layer_id)
        )
        if self.segments_layer is None:
            raise Exception(
                self.tr(
                    "Veuillez sélectionner une couche de segments valide",
                )
            )
            return

        if not isinstance(self.segments_layer, QgsVectorLayer):
            raise Exception(
                self.tr(
                    "La couche de segments n'est pas une couche vectorielle valide",
                )
            )
            return

        return self.segments_layer

    def get_compositions_layer(self):
        settings = QSettings()
        if not self.project:
            return
        self.compositions_layer_id, _ = self.project.readEntry(
            "routes_composer", "compositions_layer_id", ""
        )
        if not self.compositions_layer_id:
            return
        self.compositions_layer = cast(
            QgsVectorLayer, self.project.mapLayer(self.compositions_layer_id)
        )
        if self.compositions_layer is None:
            raise Exception(
                self.tr(
                    "Veuillez sélectionner une couche de compositions valide",
                )
            )
        if not isinstance(self.compositions_layer, QgsVectorLayer):
            raise Exception(
                self.tr(
                    "La couche de compositions n'est pas une couche vectorielle valide",
                )
            )

        return self.compositions_layer

    def get_segments_column_name(self):
        if self.project:
            self.segments_column_name, _ = self.project.readEntry(
                "routes_composer", "segments_column_name", "segments"
            )
            if self.compositions_layer is not None:
                self.segments_column_index = int(
                    self.compositions_layer.fields().indexOf(self.segments_column_name)
                )

                if self.segments_column_index == -1:
                    raise Exception(
                        self.tr(
                            "Le champ '{segments_column_name}' n'existe pas dans la couche compositions".format(
                                segments_column_name=self.segments_column_name
                            ),
                        )
                    )

            return self.segments_column_name, self.segments_column_index

    def get_id_column_name(self):
        if self.project:
            self.seg_id_column_name, _ = self.project.readEntry(
                "routes_composer", "seg_id_column_name", "id"
            )
            if self.segments_layer is not None:
                self.id_column_index = self.segments_layer.fields().indexOf(
                    self.seg_id_column_name
                )
            if self.id_column_index == -1:
                raise Exception(
                    self.tr(
                        f"Le champ {self.seg_id_column_name} n'a pas été trouvé dans la couche segments",
                    )
                )

            return self.seg_id_column_name, self.id_column_index

    def on_layer_removed(self, layer_ids):
        if self.routes_composer_connected:
            for remove_layer_id in layer_ids:
                if (
                    remove_layer_id == self.compositions_layer_id
                    or remove_layer_id == self.segments_layer_id
                ):
                    try:
                        log("layer followed removed")
                        from .ui.main_dialog.main import RoutesComposerDialog

                        dialog = RoutesComposerDialog.get_instance()
                        dialog.event_handlers.stop_running_routes_composer()

                        if dialog.ui.geom_checkbox.isChecked():
                            dialog.ui.geom_checkbox.setChecked(False)
                    except Exception as e:
                        log(f"Error removing layer: {e}")
