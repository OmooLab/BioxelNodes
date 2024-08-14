from pathlib import Path
import bpy
import re

import numpy as np

from ..bioxel.layer import Layer
from ..utils import copy_to_dir
from ..customnodes.nodes import AddCustomNode
from ..bioxelutils.utils import (get_container_obj,
                                 get_layer_prop_value,
                                 get_container_layer_objs,
                                 get_node_type, set_layer_prop_value)
from ..bioxelutils.layer import layer_to_obj, obj_to_layer
from .utils import get_cache_dir, get_layer_item_label, get_layer_label, get_preferences
from ..nodes import custom_nodes


def get_label_layer_selection(self, context):
    items = [("None", "None", "")]
    container_obj = get_container_obj(bpy.context.active_object)

    for layer_obj in get_container_layer_objs(container_obj):
        if get_layer_prop_value(layer_obj, "kind") == "label":
            items.append((layer_obj.name,
                          layer_obj.name,
                          ""))

    return items


def get_selected_objs_in_node_tree(context):
    select_objs = []
    # node_group = context.space_data.edit_tree
    for node in context.selected_nodes:
        if get_node_type(node) == "BioxelNodes_FetchLayer":
            layer_obj = node.inputs[0].default_value
            if layer_obj != None:
                cache_filepath = Path(bpy.path.abspath(
                    layer_obj.data.filepath)).resolve()
                if cache_filepath.is_file():
                    select_objs.append(layer_obj)
    return select_objs


class LayerOperator():
    bl_options = {'UNDO'}
    layer_obj_name: bpy.props.StringProperty(
        options={"HIDDEN"})  # type: ignore

    @property
    def layer_obj(self):
        return bpy.data.objects.get(self.layer_obj_name)

    @property
    def is_lost(self):
        if self.layer_obj is None:
            return None

        cache_filepath = Path(bpy.path.abspath(
            self.layer_obj.data.filepath)).resolve()
        return not cache_filepath.is_file()


class FetchLayer(bpy.types.Operator, LayerOperator, AddCustomNode):
    bl_idname = "bioxelnodes.fetch_layer"
    bl_label = "Fetch Layer"
    bl_description = "Fetch Layer"
    bl_icon = "NODE"

    def execute(self, context):
        if self.layer_obj == None:
            self.report({"WARNING"}, "Get no layer.")
            return {'FINISHED'}

        if self.is_lost:
            self.report({"WARNING"}, "Selected layer is lost.")
            return {'FINISHED'}

        self.get_node_tree(self.node_type, self.node_link)
        prev_context = bpy.context.area.type
        bpy.context.area.type = 'NODE_EDITOR'
        bpy.ops.node.add_node('INVOKE_DEFAULT',
                              type='GeometryNodeGroup',
                              use_transform=True)
        bpy.context.area.type = prev_context
        node = bpy.context.active_node

        self.assign_node_tree(node)
        node.show_options = False
        layer_obj = self.layer_obj
        node.inputs[0].default_value = layer_obj
        node.label = get_layer_label(layer_obj)

        return {"FINISHED"}

    def invoke(self, context, event):
        self.nodes_file = custom_nodes.nodes_file
        self.node_type = "BioxelNodes_FetchLayer"
        return self.execute(context)


class FetchLayerMenu(bpy.types.Menu):
    bl_idname = "BIOXELNODES_MT_ADD_LAYER"
    bl_label = "Fetch Layer"

    def draw(self, context):
        container_obj = get_container_obj(bpy.context.active_object)
        layer_objs = get_container_layer_objs(container_obj)
        layout = self.layout

        for layer_obj in layer_objs:
            op = layout.operator(FetchLayer.bl_idname,
                                 text=get_layer_item_label(context, layer_obj))
            op.layer_obj_name = layer_obj.name


class ModifyLayerOperator(LayerOperator):
    def layer_operate(self, orig_layer: Layer):
        """do the operation"""
        return orig_layer

    def add_layer_node(self, context, layer):
        layer_obj = layer_to_obj(layer,
                                 container_obj=self.layer_obj.parent,
                                 cache_dir=get_cache_dir(context))

        bpy.ops.bioxelnodes.fetch_layer('INVOKE_DEFAULT',
                                        layer_obj_name=layer_obj.name)

    def execute(self, context):
        if self.layer_obj == None:
            self.report({"WARNING"}, "Get no layer.")
            return {'FINISHED'}

        if self.is_lost:
            self.report({"WARNING"}, "Selected layer is lost.")
            return {'FINISHED'}

        orig_layer = obj_to_layer(self.layer_obj)
        new_layer = self.layer_operate(orig_layer)
        self.add_layer_node(context, new_layer)
        return {'FINISHED'}


class ResampleScalar(bpy.types.Operator, ModifyLayerOperator):
    bl_idname = "bioxelnodes.resample_scalar"
    bl_label = "Resample Scalar"
    bl_description = "Resample Scalar"
    bl_icon = "ALIASED"

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

    def layer_operate(self, orig_layer: Layer):
        modified_layer = orig_layer.copy()
        new_shape = self.get_new_shape(modified_layer.shape,
                                       modified_layer.bioxel_size[0],
                                       self.bioxel_size)

        modified_layer.resize(new_shape)
        modified_layer.name = f"{orig_layer.name}_R-{self.bioxel_size:.2f}"
        return modified_layer

    def draw(self, context):
        orig_shape = get_layer_prop_value(self.layer_obj, "shape")
        orig_size = get_layer_prop_value(self.layer_obj, "bioxel_size")
        new_shape = self.get_new_shape(orig_shape,
                                       orig_size,
                                       self.bioxel_size)

        orig_shape = tuple(orig_shape)
        bioxel_count = new_shape[0] * new_shape[1] * new_shape[2]

        layer_shape_text = f"Shape from {str(orig_shape)} to {str(new_shape)}"
        if bioxel_count > 100000000:
            layer_shape_text += "**TOO LARGE!**"

        layout = self.layout
        layout.prop(self, "bioxel_size")
        layout.label(text=layer_shape_text)

    def invoke(self, context, event):
        if self.layer_obj:
            bioxel_size = get_layer_prop_value(self.layer_obj, "bioxel_size")

            self.bioxel_size = bioxel_size
            context.window_manager.invoke_props_dialog(self,
                                                       width=400,
                                                       title=f"Resample {self.layer_obj.name}")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class SignScalar(bpy.types.Operator, ModifyLayerOperator):
    bl_idname = "bioxelnodes.sign_scalar"
    bl_label = "Sign Scalar"
    bl_description = "Sign the scalar value"
    bl_icon = "REMOVE"

    def layer_operate(self, orig_layer: Layer):
        modified_layer = orig_layer.copy()
        modified_layer.data = -orig_layer.data
        modified_layer.name = f"{orig_layer.name}_Sign"
        return modified_layer

    def invoke(self, context, event):
        if self.layer_obj:
            context.window_manager.invoke_confirm(self,
                                                  event,
                                                  message=f"Are you sure to sign {self.layer_obj.name}?")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class FillOperator(ModifyLayerOperator):

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
        if self.layer_obj:
            scalar_min = get_layer_prop_value(self.layer_obj, "min")

            self.fill_value = min(scalar_min, 0)
            context.window_manager.invoke_props_dialog(self,
                                                       width=400,
                                                       title=f"Fill {self.layer_obj.name}")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class FillByThreshold(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_threshold"
    bl_label = "Fill Value by Threshold"
    bl_description = "Fill Value by Threshold"
    bl_icon = "EMPTY_SINGLE_ARROW"

    threshold: bpy.props.FloatProperty(
        name="Threshold",
        soft_min=0, soft_max=1024,
        default=128,
    )  # type: ignore

    def layer_operate(self, orig_layer: Layer):
        data = np.amax(orig_layer.data, -1)
        mask = data <= self.threshold \
            if self.invert else data > self.threshold

        modified_layer = orig_layer.copy()
        modified_layer.fill(self.fill_value, mask)
        modified_layer.name = f"{orig_layer.name}_F-{self.threshold}"
        return modified_layer


class FillByRange(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_range"
    bl_label = "Fill Value by Range"
    bl_description = "Fill Value by Range"
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

    def layer_operate(self, orig_layer: Layer):
        data = np.amax(orig_layer.data, -1)
        mask = (data <= self.from_min) | (data >= self.from_max) if self.invert else \
            (data > self.from_min) & (data < self.from_max)

        modified_layer = orig_layer.copy()
        modified_layer.fill(self.fill_value, mask)
        modified_layer.name = f"{orig_layer.name}_F-{self.from_min}-{self.from_max}"
        return modified_layer


class FillByLabel(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_label"
    bl_label = "Fill Value by Label"
    bl_description = "Fill Value by Label Area"
    bl_icon = "MESH_CAPSULE"

    label_obj_name: bpy.props.EnumProperty(name="Label Layer",
                                           items=get_label_layer_selection)  # type: ignore

    def layer_operate(self, orig_layer: Layer):
        label_obj = bpy.data.objects.get(self.label_obj_name)
        if not label_obj:
            self.report({"WARNING"}, "Cannot find any label layer.")
            return {'FINISHED'}

        label_layer = obj_to_layer(label_obj)
        label_layer.resize(orig_layer.shape)
        mask = np.amax(label_layer.data, -1)
        if self.invert:
            mask = 1 - mask

        modified_layer = orig_layer.copy()
        modified_layer.fill(self.fill_value, mask)
        modified_layer.name = f"{orig_layer.name}_F-{label_layer.name}"
        return modified_layer


class CombineLabels(bpy.types.Operator, ModifyLayerOperator):
    bl_idname = "bioxelnodes.combine_labels"
    bl_label = "Combine Labels"
    bl_description = "Combine all selected labels"
    bl_icon = "MOD_BUILD"

    def execute(self, context):
        label_objs = [obj for obj in get_selected_objs_in_node_tree(context)
                      if get_layer_prop_value(obj, "kind") == "label"]

        if len(label_objs) < 2:
            self.report({"WARNING"}, "Not enough layers.")
            return {'FINISHED'}
        base_obj = label_objs[0]
        label_objs = label_objs[1:]

        base_layer = obj_to_layer(base_obj)
        modified_layer = base_layer.copy()
        label_names = [base_layer.name]

        for label_obj in label_objs:
            label_layer = obj_to_layer(label_obj)
            label_layer.resize(base_layer.shape)
            modified_layer.data = np.maximum(
                modified_layer.data, label_layer.data)
            label_names.append(label_layer.name)

        modified_layer.name = f"C-{'-'.join(label_names)}"

        self.add_layer_node(context, modified_layer)
        return {'FINISHED'}


class SaveLayerCache(bpy.types.Operator, LayerOperator):
    bl_idname = "bioxelnodes.save_layer_cache"
    bl_label = "Save Layer Cache"
    bl_description = "Save Layer Cache"
    bl_icon = "FILE_TICK"

    cache_dir: bpy.props.StringProperty(
        name="Cache Directory",
        subtype='DIR_PATH',
        default="//"
    )  # type: ignore

    def execute(self, context):
        if self.layer_obj == None:
            self.report({"WARNING"}, "Get no layer.")
            return {'FINISHED'}

        if self.is_lost:
            self.report({"WARNING"}, "Selected layer is lost.")
            return {'FINISHED'}

        # "//"
        output_dir = bpy.path.abspath(self.cache_dir)
        source_dir = bpy.path.abspath(self.layer_obj.data.filepath)

        source_path: Path = Path(source_dir).resolve()
        is_sequence = self.layer_obj.data.is_sequence

        name = self.layer_obj.name if is_sequence else f"{self.layer_obj.name}.vdb"
        output_path: Path = Path(output_dir, name, source_path.name).resolve() \
            if is_sequence else Path(output_dir, name).resolve()

        if output_path != source_path:
            copy_to_dir(source_path.parent if is_sequence else source_path,
                        output_path.parent.parent if is_sequence else output_path.parent,
                        new_name=name)

        blend_path = Path(bpy.path.abspath("//")).resolve()

        self.layer_obj.data.filepath = bpy.path.relpath(str(output_path),
                                                        start=str(blend_path))

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.layer_obj:
            context.window_manager.invoke_props_dialog(self,
                                                       width=500)
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class RenameLayer(bpy.types.Operator, LayerOperator):
    bl_idname = "bioxelnodes.rename_layer"
    bl_label = "Rename Layer"
    bl_description = "Rename Layer"
    bl_icon = "FILE_FONT"

    name: bpy.props.StringProperty(name="New Name")  # type: ignore

    def execute(self, context):
        if self.layer_obj == None:
            self.report({"WARNING"}, "Get no layer.")
            return {'FINISHED'}

        if self.is_lost:
            self.report({"WARNING"}, "Selected layer is lost.")
            return {'FINISHED'}

        name = f"{self.layer_obj.parent.name}_{self.name}"
        self.layer_obj.name = name
        self.layer_obj_name = name
        self.layer_obj.data.name = name

        set_layer_prop_value(self.layer_obj, "name", self.name)

        node_group = context.space_data.edit_tree
        for node in node_group.nodes:
            if get_node_type(node) == "BioxelNodes_FetchLayer":
                if node.inputs[0].default_value == self.layer_obj:
                    node.label = self.name

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.layer_obj:
            self.name = get_layer_prop_value(self.layer_obj, "name")
            context.window_manager.invoke_props_dialog(self,
                                                       width=500,
                                                       title=f"rename {self.layer_obj.name}")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class RemoveLayer(bpy.types.Operator, LayerOperator):
    bl_idname = "bioxelnodes.remove_layer"
    bl_label = "Remove Selected Layer"
    bl_description = "Remove Layer"
    bl_icon = "TRASH"

    def execute(self, context):
        if self.layer_obj == None:
            self.report({"WARNING"}, "Get no layer.")
            return {'FINISHED'}

        node_group = context.space_data.edit_tree
        for node in node_group.nodes:
            if get_node_type(node) == "BioxelNodes_FetchLayer":
                if node.inputs[0].default_value == self.layer_obj:
                    node_group.nodes.remove(node)

        cache_filepath = Path(bpy.path.abspath(
            self.layer_obj.data.filepath)).resolve()

        if cache_filepath.is_file():
            if self.layer_obj.data.is_sequence:
                for f in cache_filepath.parent.iterdir():
                    f.unlink(missing_ok=True)
            else:
                cache_filepath.unlink(missing_ok=True)

        # also remove layer object
        bpy.data.volumes.remove(self.layer_obj.data)

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.layer_obj:
            context.window_manager.invoke_confirm(self,
                                                  event,
                                                  message=f"Are you sure to remove {self.layer_obj.name}?")
            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)


class RemoveMissingLayers(bpy.types.Operator):
    bl_idname = "bioxelnodes.remove_lost_layers"
    bl_label = "Remove All Missing Layers"
    bl_description = "Remove all missing "
    bl_icon = "BRUSH_DATA"

    def execute(self, context):
        container_obj = context.object
        for layer_obj in get_container_layer_objs(container_obj):
            cache_filepath = Path(bpy.path.abspath(
                layer_obj.data.filepath)).resolve()
            if cache_filepath.is_file():
                continue
            bpy.ops.bioxelnodes.remove_layer('EXEC_DEFAULT',
                                             layer_obj_name=layer_obj.name)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_confirm(self,
                                              event,
                                              message=f"Are you sure to remove all **Missing** layers?")
        return {'RUNNING_MODAL'}
