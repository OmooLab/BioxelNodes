from pathlib import Path
import bpy

import numpy as np



from ..exceptions import NoContent
from ..bioxel.layer import Layer
from ..bioxelutils.node import add_node_to_graph
from ..bioxelutils.common import (get_container_obj, get_layer_kind, get_layer_label, get_layer_name,
                                  get_layer_prop_value,
                                  get_container_layer_objs,
                                  get_node_type, is_missing_layer, move_node_to_node, set_layer_prop_value)
from ..bioxelutils.layer import layer_to_obj, obj_to_layer
from ..utils import get_cache_dir, copy_to_dir, get_use_link


def get_label_layer_selection(self, context):
    items = [("None", "None", "")]
    container_obj = get_container_obj(bpy.context.active_object)

    for layer_obj in get_container_layer_objs(container_obj):
        kind = get_layer_prop_value(layer_obj, "kind")
        name = get_layer_prop_value(layer_obj, "name")
        if kind == "label":
            items.append((layer_obj.name,
                          name,
                          ""))

    return items


class FetchLayer(bpy.types.Operator):
    bl_idname = "bioxelnodes.fetch_layer"
    bl_label = "Fetch Layer"
    bl_description = "Fetch layer from current container"
    bl_icon = "NODE"
    bl_options = {'UNDO'}

    layer_obj_name: bpy.props.StringProperty(
        options={"HIDDEN"})  # type: ignore

    @classmethod
    def description(cls, context, properties):
        layer_obj_name = properties.layer_obj_name
        layer_obj = bpy.data.objects.get(layer_obj_name)
        return "\n".join([f"{prop}: {get_layer_prop_value(layer_obj, prop)}"
                          for prop in ["kind",
                                       "bioxel_size",
                                       "shape",
                                       "frame_count",
                                       "channel_count",
                                       "min", "max"]])

    @property
    def layer_obj(self):
        return bpy.data.objects.get(self.layer_obj_name)

    def execute(self, context):
        if self.layer_obj == None:
            self.report({"WARNING"}, "Get no layer.")
            return {'FINISHED'}

        if is_missing_layer(self.layer_obj):
            self.report({"WARNING"}, "Selected layer is lost.")
            return {'FINISHED'}

        bpy.ops.bioxelnodes.add_node('EXEC_DEFAULT',
                                     node_name="FetchLayer",
                                     node_label="Fetch Layer")
        node = bpy.context.active_node

        node.inputs[0].default_value = self.layer_obj
        node.label = get_layer_label(self.layer_obj)

        return {"FINISHED"}


def get_selected_layers(context, layer_filter=None):
    def _layer_filter(layer_obj, context):
        return True

    layer_filter = layer_filter or _layer_filter
    select_objs = []
    # node_group = context.space_data.edit_tree
    for node in context.selected_nodes:
        if get_node_type(node) == "BioxelNodes_FetchLayer":
            layer_obj = node.inputs[0].default_value
            if layer_obj is not None:
                if layer_filter(layer_obj, context):
                    select_objs.append(layer_obj)

    return list(set(select_objs))


def get_selected_layer(context, layer_filter=None):
    layer_objs = get_selected_layers(context, layer_filter)
    return layer_objs[0] if len(layer_objs) > 0 else None


class OutputLayerOperator():
    new_layer_name: bpy.props.StringProperty(name="New Name",
                                             options={"SKIP_SAVE"})  # type: ignore

    def operate(self, orig_layer: Layer, context):
        """do the operation"""
        return orig_layer

    def add_layer_node(self, context, layer):
        orig_node = context.selected_nodes[0]
        layer_obj = layer_to_obj(layer,
                                 container_obj=context.object,
                                 cache_dir=get_cache_dir())
        node_group = context.space_data.edit_tree
        fetch_node = add_node_to_graph("FetchLayer",
                                       node_group,
                                       use_link=get_use_link())
        fetch_node.label = get_layer_prop_value(layer_obj, "name")
        fetch_node.inputs[0].default_value = layer_obj
        move_node_to_node(fetch_node, orig_node, (0, -100))

    def execute(self, context):
        layer_obj = get_selected_layer(context)
        if layer_obj == None:
            self.report({"WARNING"}, "Get no layer.")
            return {'FINISHED'}

        if is_missing_layer(layer_obj):
            self.report({"WARNING"}, "Selected layer is lost.")
            return {'FINISHED'}

        orig_layer = obj_to_layer(layer_obj)
        try:
            new_layer = self.operate(orig_layer, context)
        except NoContent as e:
            self.report({"WARNING"}, e.message)
            return {'FINISHED'}

        self.add_layer_node(context, new_layer)
        return {'FINISHED'}


class LayerOperator():

    def operate(self, layer_obj: bpy.types.Object, context):
        """do the operation"""
        ...

    def execute(self, context):
        layer_obj = get_selected_layer(context)
        if layer_obj == None:
            self.report({"WARNING"}, "Get no layer.")
            return {'FINISHED'}

        if is_missing_layer(layer_obj):
            self.report({"WARNING"}, "Selected layer is lost.")
            return {'FINISHED'}

        self.operate(layer_obj, context)

        return {'FINISHED'}


class RetimeLayer(bpy.types.Operator, LayerOperator):
    bl_idname = "bioxelnodes.retime_layer"
    bl_label = "Retime Sequence"
    bl_description = "Retime layer time sequence"
    bl_icon = "TIME"

    frame_duration: bpy.props.IntProperty(name="Frames")  # type: ignore
    frame_start: bpy.props.IntProperty(name="Start")  # type: ignore
    frame_offset: bpy.props.IntProperty(name="Offset")  # type: ignore
    sequence_mode: bpy.props.EnumProperty(name="Mode",
                                          default="REPEAT",
                                          items=[("CLIP", "Clip", ""),
                                                 ("EXTEND", "Extend", ""),
                                                 ("REPEAT", "Repeat", ""),
                                                 ("PING_PONG", "Ping-Pong", "")])  # type: ignore

    def operate(self, layer_obj, context):
        layer_obj.data.frame_duration = self.frame_duration
        layer_obj.data.frame_start = self.frame_start
        layer_obj.data.frame_offset = self.frame_offset
        layer_obj.data.sequence_mode = self.sequence_mode

    def invoke(self, context, event):
        layer_obj = get_selected_layer(context)
        if layer_obj:
            self.frame_duration = layer_obj.data.frame_duration
            self.frame_start = layer_obj.data.frame_start
            self.frame_offset = layer_obj.data.frame_offset
            self.sequence_mode = layer_obj.data.sequence_mode
            name = get_layer_label(layer_obj)
            context.window_manager.invoke_props_dialog(self,
                                                       title=f"Retime {name}")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class RelocateLayer(bpy.types.Operator, LayerOperator):
    bl_idname = "bioxelnodes.relocate_layer"
    bl_label = "Relocate Layer Cache"
    bl_description = "Relocate layer cache"
    bl_icon = "FILE"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore

    def operate(self, layer_obj, context):
        layer_obj.data.filepath = self.filepath

    def invoke(self, context, event):
        layer_obj = get_selected_layer(context)
        if layer_obj:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class RenameLayer(bpy.types.Operator, LayerOperator):
    bl_idname = "bioxelnodes.rename_layer"
    bl_label = "Rename Layer"
    bl_description = "Rename layer"
    bl_icon = "FILE_FONT"

    new_name: bpy.props.StringProperty(name="New Name",
                                       options={"SKIP_SAVE"})  # type: ignore

    def operate(self, layer_obj, context):
        name = f"{layer_obj.parent.name}_{self.new_name}"
        layer_obj.name = name
        layer_obj.data.name = name

        set_layer_prop_value(layer_obj, "name", self.new_name)

        node_group = context.space_data.edit_tree
        for node in node_group.nodes:
            if get_node_type(node) == "BioxelNodes_FetchLayer":
                if node.inputs[0].default_value == layer_obj:
                    node.label = self.new_name

    def invoke(self, context, event):
        layer_obj = get_selected_layer(context)
        if layer_obj:
            self.new_name = get_layer_name(layer_obj)
            name = get_layer_label(layer_obj)
            context.window_manager.invoke_props_dialog(self,
                                                       title=f"Rename {name}")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class ResampleLayer(bpy.types.Operator, OutputLayerOperator):
    bl_idname = "bioxelnodes.resample_layer"
    bl_label = "Resample Value"
    bl_description = "Resample value"
    bl_icon = "ALIASED"

    smooth: bpy.props.IntProperty(name="Smooth Iteration",
                                  default=0,
                                  soft_min=0, soft_max=5,
                                  options={"SKIP_SAVE"})  # type: ignore

    bioxel_size: bpy.props.FloatProperty(
        name="Bioxel Size",
        soft_min=0.1, soft_max=10.0,
        default=1,
    )  # type: ignore

    @staticmethod
    def get_new_shape(orig_shape, orig_size, new_size):
        return (int(orig_shape[0]*orig_size/new_size),
                int(orig_shape[1]*orig_size/new_size),
                int(orig_shape[2]*orig_size/new_size))

    def operate(self, orig_layer: Layer, context):
        new_layer = orig_layer.copy()
        new_shape = self.get_new_shape(new_layer.shape,
                                       new_layer.bioxel_size[0],
                                       self.bioxel_size)

        new_layer.resize(new_shape, self.smooth)
        new_layer.name = self.new_layer_name \
            or f"{orig_layer.name}_R-{self.bioxel_size:.2f}"
        return new_layer

    def draw(self, context):
        layer_obj = get_selected_layer(context)
        orig_shape = get_layer_prop_value(layer_obj, "shape")
        orig_size = get_layer_prop_value(layer_obj, "bioxel_size")
        new_shape = self.get_new_shape(orig_shape,
                                       orig_size,
                                       self.bioxel_size)

        orig_shape = tuple(orig_shape)
        bioxel_count = new_shape[0] * new_shape[1] * new_shape[2]

        layer_shape_text = f"Shape from {str(orig_shape)} to {str(new_shape)}"
        if bioxel_count > 100000000:
            layer_shape_text += "**TOO LARGE!**"

        layout = self.layout
        layout.prop(self, "new_layer_name")
        layout.prop(self, "bioxel_size")
        layout.prop(self, "smooth")
        layout.label(text=layer_shape_text)

    def invoke(self, context, event):
        layer_obj = get_selected_layer(context)
        if layer_obj:
            name = get_layer_label(layer_obj)
            self.bioxel_size = get_layer_prop_value(layer_obj,
                                                    "bioxel_size")
            context.window_manager.invoke_props_dialog(self,
                                                       title=f"Resample {name}")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class SignScalar(bpy.types.Operator, OutputLayerOperator):
    bl_idname = "bioxelnodes.sign_scalar"
    bl_label = "Sign Value"
    bl_description = "Sign value"
    bl_icon = "REMOVE"

    def operate(self, orig_layer: Layer, context):
        new_layer = orig_layer.copy()
        new_layer.data = -orig_layer.data
        new_layer.name = self.new_layer_name \
            or f"{orig_layer.name}_Sign"
        return new_layer

    def invoke(self, context, event):
        layer_obj = get_selected_layer(context)
        if layer_obj:
            name = get_layer_label(layer_obj)
            context.window_manager.invoke_props_dialog(self,
                                                       title=f"Sign {name}")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class FillOperator(OutputLayerOperator):

    fill_value: bpy.props.FloatProperty(
        name="Fill Value",
        soft_min=0, soft_max=1024.0,
        default=0,
    )  # type: ignore

    invert: bpy.props.BoolProperty(
        name="Invert Aera",
        default=True,
    )  # type: ignore

    def invoke(self, context, event):
        layer_obj = get_selected_layer(context)
        if layer_obj:
            scalar_min = get_layer_prop_value(layer_obj, "min")
            self.fill_value = min(scalar_min, 0)
            name = get_layer_label(layer_obj)
            context.window_manager.invoke_props_dialog(self,
                                                       title=f"Fill {name}")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class FillByThreshold(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_threshold"
    bl_label = "Fill Value by Threshold"
    bl_description = "Fill value by threshold"
    bl_icon = "EMPTY_SINGLE_ARROW"

    threshold: bpy.props.FloatProperty(
        name="Threshold",
        soft_min=0, soft_max=1024,
        default=128,
    )  # type: ignore

    def operate(self, orig_layer: Layer, context):
        data = np.amax(orig_layer.data, -1)
        mask = data <= self.threshold \
            if self.invert else data > self.threshold

        new_layer = orig_layer.copy()
        new_layer.fill(self.fill_value, mask, 3)
        new_layer.name = self.new_layer_name \
            or f"{orig_layer.name}_F-{self.threshold:.2f}"
        return new_layer


class FillByRange(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_range"
    bl_label = "Fill Value by Range"
    bl_description = "Fill value by range"
    bl_icon = "IPO_CONSTANT"

    from_min: bpy.props.FloatProperty(
        name="From Min",
        soft_min=0, soft_max=1024,
        default=128,
    )  # type: ignore

    from_max: bpy.props.FloatProperty(
        name="From Max",
        soft_min=0, soft_max=1024,
        default=256,
    )  # type: ignore

    def operate(self, orig_layer: Layer, context):
        data = np.amax(orig_layer.data, -1)
        mask = (data <= self.from_min) | (data >= self.from_max) if self.invert else \
            (data > self.from_min) & (data < self.from_max)

        new_layer = orig_layer.copy()
        new_layer.fill(self.fill_value, mask, 3)
        new_layer.name = self.new_layer_name \
            or f"{orig_layer.name}_F-{self.from_min:.2f}-{self.from_max:.2f}"
        return new_layer


class FillByLabel(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_label"
    bl_label = "Fill Value by Label"
    bl_description = "Fill value by label"
    bl_icon = "MESH_CAPSULE"

    smooth: bpy.props.IntProperty(name="Smooth Iteration",
                                  default=0,
                                  soft_min=0, soft_max=5,
                                  options={"SKIP_SAVE"})  # type: ignore

    label_obj_name: bpy.props.EnumProperty(name="Label Layer",
                                           items=get_label_layer_selection)  # type: ignore

    def operate(self, orig_layer: Layer, context):
        label_obj = bpy.data.objects.get(self.label_obj_name)
        if label_obj is None:
            raise NoContent("Cannot find any label layer.")

        label_layer = obj_to_layer(label_obj)
        label_layer.resize(orig_layer.shape, self.smooth)
        mask = np.amax(label_layer.data, -1)
        if self.invert:
            mask = 1 - mask

        new_layer = orig_layer.copy()
        new_layer.fill(self.fill_value, mask, 3)
        new_layer.name = self.new_layer_name \
            or f"{orig_layer.name}_F-{label_layer.name}"
        return new_layer


class CombineLabels(bpy.types.Operator, OutputLayerOperator):
    bl_idname = "bioxelnodes.combine_labels"
    bl_label = "Combine Labels"
    bl_description = "Combine all selected labels"
    bl_icon = "MOD_BUILD"

    def execute(self, context):
        def layer_filter(layer_obj, context):
            return get_layer_kind(layer_obj) == "label"

        label_objs = get_selected_layers(context, layer_filter)

        if len(label_objs) < 2:
            self.report({"WARNING"}, "Not enough layers.")
            return {'FINISHED'}

        base_obj = label_objs[0]
        label_objs = label_objs[1:]

        base_layer = obj_to_layer(base_obj)
        new_layer = base_layer.copy()
        label_names = [base_layer.name]

        for label_obj in label_objs:
            label_layer = obj_to_layer(label_obj)
            label_layer.resize(base_layer.shape)
            new_layer.data = np.maximum(
                new_layer.data, label_layer.data)
            label_names.append(label_layer.name)

        new_layer.name = self.new_layer_name \
            or f"C-{'-'.join(label_names)}"

        self.add_layer_node(context, new_layer)
        return {'FINISHED'}


class BatchLayerOperator():
    success_msg = "Successfully done selected layers."
    fail_msg = "fails."

    def execute(self, context):
        layer_objs = self.get_layers(context)

        fails = []
        for layer_obj in layer_objs:
            try:
                self.operate(layer_obj, context)
            except:
                fails.append(layer_obj)

        if len(fails) == 0:
            self.report({"INFO"}, self.success_msg)
        else:
            self.report(
                {"WARNING"}, f"{','.join([layer_obj.name for layer_obj in fails])} {self.fail_msg}")

        return {'FINISHED'}


class SaveLayersCache(BatchLayerOperator):
    fail_msg = "fail to save."

    cache_dir: bpy.props.StringProperty(
        name="Cache Directory",
        subtype='DIR_PATH',
        default="//"
    )  # type: ignore

    def operate(self, layer_obj, context):
        output_dir = bpy.path.abspath(self.cache_dir)
        source_dir = bpy.path.abspath(layer_obj.data.filepath)

        source_path: Path = Path(source_dir).resolve()
        is_sequence = layer_obj.data.is_sequence

        name = layer_obj.name if is_sequence else f"{layer_obj.name}.vdb"
        output_path: Path = Path(output_dir, name, source_path.name).resolve() \
            if is_sequence else Path(output_dir, name).resolve()

        if output_path != source_path:
            copy_to_dir(source_path.parent if is_sequence else source_path,
                        output_path.parent.parent if is_sequence else output_path.parent,
                        new_name=name)

        blend_path = Path(bpy.path.abspath("//")).resolve()

        layer_obj.data.filepath = bpy.path.relpath(str(output_path),
                                                   start=str(blend_path))

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}


class RemoveLayers(BatchLayerOperator):
    fail_msg = "fail to remove."

    def operate(self, layer_obj, context):
        for node_group in bpy.data.node_groups:
            for node in node_group.nodes:
                if get_node_type(node) == "BioxelNodes_FetchLayer":
                    if node.inputs[0].default_value == layer_obj:
                        node_group.nodes.remove(node)

        cache_filepath = Path(bpy.path.abspath(
            layer_obj.data.filepath)).resolve()

        if cache_filepath.is_file():
            if layer_obj.data.is_sequence:
                for f in cache_filepath.parent.iterdir():
                    f.unlink(missing_ok=True)
            else:
                cache_filepath.unlink(missing_ok=True)

        # also remove layer object
        bpy.data.volumes.remove(layer_obj.data)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_confirm(self,
                                              event,
                                              message=f"Are you sure to remove them?")
        return {'RUNNING_MODAL'}


class SaveSelectedLayersCache(bpy.types.Operator, SaveLayersCache):
    bl_idname = "bioxelnodes.save_selected_layers_cache"
    bl_label = "Save Selected Layers Cache"
    bl_description = "Save selected layers' Cache"
    bl_icon = "FILE_TICK"

    success_msg = "Successfully saved all selected layers."

    def get_layers(self, context):
        def is_not_missing(layer_obj, context):
            return not is_missing_layer(layer_obj)
        return get_selected_layers(context, is_not_missing)


class RemoveSelectedLayers(bpy.types.Operator, RemoveLayers):
    bl_idname = "bioxelnodes.remove_selected_layers"
    bl_label = "Remove Selected Layers"
    bl_description = "Remove selected layers"
    bl_icon = "TRASH"

    success_msg = "Successfully removed all selected layers."

    def get_layers(self, context):
        return get_selected_layers(context)
