import bpy
from pathlib import Path
import shutil
from .utils import get_all_layers, get_container, get_container_layers


def save_layer(layer, output_dir):
    name = layer.name

    # "//"
    output_dir = bpy.path.abspath(output_dir)
    source_dir = bpy.path.abspath(layer.data.filepath)

    output_path: Path = Path(output_dir, f"{name}.vdb").resolve()
    source_path: Path = Path(source_dir).resolve()

    if output_path != source_path:
        shutil.copy(source_path, output_path)

    blend_path = Path(bpy.path.abspath("//")).resolve()
    layer.data.filepath = bpy.path.relpath(
        str(output_path), start=str(blend_path))


class SaveBioxelLayers(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_bioxel_layers"
    bl_label = "Save Bioxel Layers"
    bl_description = "Save Bioxel Layers to Directory."
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        container = get_container(bpy.context.active_object)
        return True if container else False

    def execute(self, context):
        container = get_container(bpy.context.active_object)

        if not container:
            self.report({"WARNING"}, "Cannot find any bioxel container.")
            return {'FINISHED'}

        for layer in get_container_layers(container):
            try:
                save_layer(layer, context.scene.bioxel_layer_dir)
            except:
                self.report(
                    {"WARNING"}, f"Fail to save {layer.name}, skiped")

        self.report({"INFO"}, f"Successfully saved bioxel layers.")

        return {'FINISHED'}


class SaveAllBioxelLayers(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_all_bioxel_layers"
    bl_label = "Save All Bioxel Layers"
    bl_description = "Save All Bioxel Layers to Directory."
    bl_options = {'UNDO'}

    def execute(self, context):

        layers = get_all_layers()

        if len(layers) == 0:
            self.report({"WARNING"}, "Cannot find any bioxel layer.")
            return {'FINISHED'}

        for layer in layers:
            try:
                save_layer(layer, context.scene.bioxel_layer_dir)
            except:
                self.report(
                    {"WARNING"}, f"Fail to save {layer.name}, skiped")

        self.report({"INFO"}, f"Successfully saved bioxel layers.")

        return {'FINISHED'}


class BIOXELNODES_PT_Bioxels(bpy.types.Panel):
    bl_idname = "BIOXELNODES_PT_Bioxels"
    bl_label = "Bioxel Nodes"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, 'bioxel_layer_dir')
        layout.operator(SaveAllBioxelLayers.bl_idname)
