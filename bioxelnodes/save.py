import bpy
from pathlib import Path
import shutil
from .utils import get_all_layers, get_container, get_container_layers
from .nodes import custom_nodes

CLASS_PREFIX = "BIOXELNODES_MT_NODES"


class ReLinkNodes(bpy.types.Operator):
    bl_idname = "bioxelnodes.relink_nodes"
    bl_label = "Relink Nodes to Addon"
    bl_description = "Relink all nodes to addon source"

    def execute(self, context):
        file_name = Path(custom_nodes.nodes_file).name
        for lib in bpy.data.libraries:
            lib_path = Path(bpy.path.abspath(lib.filepath)).resolve()
            lib_name = lib_path.name
            if lib_name == file_name:
                if str(lib_path) != custom_nodes.nodes_file:
                    lib.filepath = custom_nodes.nodes_file

        self.report({"INFO"}, f"Successfully relinked.")

        return {'FINISHED'}


class SaveAllToShare(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_all_to_share"
    bl_label = "Save All Staged Data"
    bl_description = "Save all staged data for sharing"

    layer_dir: bpy.props.StringProperty(
        name="Layer Directory",
        subtype='DIR_PATH',
        default="//"
    )  # type: ignore

    save_node: bpy.props.BoolProperty(
        name="Save Node Library File",
        default=True,
    )  # type: ignore

    node_file_dir: bpy.props.StringProperty(
        name="Library Directory",
        subtype='DIR_PATH',
        default="//"
    )  # type: ignore

    def execute(self, context):
        files = []
        for classname in dir(bpy.types):
            if CLASS_PREFIX in classname:
                cls = getattr(bpy.types, classname)
                files.append(cls.nodes_file)
        files = list(set(files))

        for file in files:
            file_name = Path(file).name
            # "//"
            node_file_dir = bpy.path.abspath(self.node_file_dir)

            output_path: Path = Path(node_file_dir, file_name).resolve()
            source_path: Path = Path(file).resolve()

            if output_path != source_path:
                shutil.copy(source_path, output_path)

            for lib in bpy.data.libraries:
                lib_path = Path(bpy.path.abspath(lib.filepath)).resolve()
                if lib_path == source_path:
                    blend_path = Path(bpy.path.abspath("//")).resolve()
                    lib.filepath = bpy.path.relpath(
                        str(output_path), start=str(blend_path))

            self.report({"INFO"}, f"Successfully saved to {output_path}")

        layers = get_all_layers()
        for layer in layers:
            try:
                save_layer(layer, self.layer_dir)
            except:
                self.report(
                    {"WARNING"}, f"Fail to save {layer.name}, skiped")

        self.report({"INFO"}, f"Successfully saved bioxel layers.")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self,
                                                   width=500)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def draw(self, context):
        layout = self.layout
        panel = layout.box()
        panel.prop(self, "layer_dir")
        panel = layout.box()
        panel.prop(self, "save_node")
        panel.prop(self, "node_file_dir")
        layout.label(text="Save your blender file first.")


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


class SaveLayers(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_layers"
    bl_label = "Save Container's Layers"
    bl_description = "Save Bioxel Layers to Directory."

    layer_dir: bpy.props.StringProperty(
        name="Layer Directory",
        subtype='DIR_PATH',
        default="//"
    )  # type: ignore

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
                save_layer(layer, self.layer_dir)
            except:
                self.report(
                    {"WARNING"}, f"Fail to save {layer.name}, skiped")

        self.report({"INFO"}, f"Successfully saved bioxel layers.")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self,
                                                   width=500)
        return {'RUNNING_MODAL'}
