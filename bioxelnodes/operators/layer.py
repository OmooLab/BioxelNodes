from pathlib import Path
import bpy

import numpy as np


from ..bioxel.layer import Layer
from ..bioxelutils.node import get_nodes_by_type
from ..bioxelutils.container import add_layers, get_container_obj
from ..bioxelutils.layer import obj_to_layer, get_container_layer_objs, get_layer_obj
from .utils import get_preferences, select_object


def get_layer_prop_value(layer_obj: bpy.types.Object, prop: str):
    try:
        node_group = layer_obj.modifiers[0].node_group
        layer_node = get_nodes_by_type(node_group, "BioxelNodes__Layer")[0]
        return layer_node.inputs[prop].default_value
    except:
        return None


def get_label_layer_selection(self, context):
    items = [("None", "None", "")]
    container_obj = get_container_obj(bpy.context.active_object)

    for layer_obj in get_container_layer_objs(container_obj):
        if get_layer_prop_value(layer_obj, "kind") == "label":
            items.append((layer_obj.name,
                          layer_obj.name,
                          ""))

    return items


class LayerOperator():
    bl_options = {'UNDO'}
    base_obj: bpy.types.Object = None

    def add_layer(self, context, layer):
        preferences = get_preferences(context)
        cache_dir = Path(preferences.cache_dir, 'VDBs')
        container_obj = self.base_obj.parent

        add_layers([layer],
                   container_obj,
                   cache_dir)

        select_object(container_obj)

    def invoke(self, context, event):
        self.base_obj = get_layer_obj(bpy.context.active_object)
        return self.execute(context)


class ScalarOperator(LayerOperator):
    @classmethod
    def poll(cls, context):
        label_objs = [obj for obj in context.selected_ids
                      if get_layer_prop_value(obj, "kind") == "scalar"]
        return True if len(label_objs) > 0 else False


class LabelOperator(LayerOperator):
    @classmethod
    def poll(cls, context):
        label_objs = [obj for obj in context.selected_ids
                      if get_layer_prop_value(obj, "kind") == "label"]
        return True if len(label_objs) > 0 else False


class SignScalar(bpy.types.Operator, ScalarOperator):
    bl_idname = "bioxelnodes.sign_scalar"
    bl_label = "Sign Scalar"
    bl_description = "Sign the scalar value"

    def execute(self, context):
        base_layer = obj_to_layer(self.base_obj)

        modified_layer = base_layer.copy()
        modified_layer.data = -base_layer.data
        modified_layer.name = f"{base_layer.name}_Signed"

        self.add_layer(context, modified_layer)
        return {'FINISHED'}


class FillOperator(ScalarOperator):
    def invoke(self, context, event):
        self.base_obj = get_layer_obj(bpy.context.active_object)
        scalar_min = get_layer_prop_value(self.base_obj, "min")
        self.fill_value = min(scalar_min, 0)
        context.window_manager.invoke_props_dialog(self, width=400)
        return {'RUNNING_MODAL'}


class FillByThreshold(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_threshold"
    bl_label = "Fill Value by Threshold"
    bl_description = "Fill Value by Threshold"

    threshold: bpy.props.FloatProperty(
        name="Threshold",
        soft_min=0, soft_max=1024,
        default=128,
    )  # type: ignore

    fill_value: bpy.props.FloatProperty(
        name="Fill Value",
        soft_min=0, soft_max=1024.0,
        default=0,
    )  # type: ignore

    invert: bpy.props.BoolProperty(
        name="Invert Area",
        default=True,
    )  # type: ignore

    def execute(self, context):
        base_layer = obj_to_layer(self.base_obj)

        data = np.amax(base_layer.data, -1)
        mask = data <= self.threshold \
            if self.invert else data > self.threshold

        modified_layer = base_layer.copy()
        modified_layer.fill(self.fill_value, mask)
        modified_layer.name = f"{base_layer.name}_{self.threshold}-Filled"

        self.add_layer(context, modified_layer)

        return {'FINISHED'}


class FillByRange(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_range"
    bl_label = "Fill Value by Range"
    bl_description = "Fill Value by Range"

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

    fill_value: bpy.props.FloatProperty(
        name="Fill Value",
        soft_min=0, soft_max=1024.0,
        default=0,
    )  # type: ignore

    invert: bpy.props.BoolProperty(
        name="Invert Area",
        default=True,
    )  # type: ignore

    def execute(self, context):
        base_layer = obj_to_layer(self.base_obj)

        data = np.amax(base_layer.data, -1)
        mask = (data <= self.from_min) | (data >= self.from_max) if self.invert else \
            (data > self.from_min) & (data < self.from_max)

        modified_layer = base_layer.copy()
        modified_layer.fill(self.fill_value, mask)
        modified_layer.name = f"{base_layer.name}_{self.from_min}-{self.from_max}-Filled"

        self.add_layer(context, modified_layer)
        return {'FINISHED'}


class FillByLabel(bpy.types.Operator, FillOperator):
    bl_idname = "bioxelnodes.fill_by_label"
    bl_label = "Fill Value by Label"
    bl_description = "Fill Value by Label Area"

    label_obj_name: bpy.props.EnumProperty(
        name="Label Layer",
        items=get_label_layer_selection
    )  # type: ignore

    fill_value: bpy.props.FloatProperty(
        name="Fill Value",
        soft_min=0, soft_max=1024.0,
        default=0,
    )  # type: ignore

    invert: bpy.props.BoolProperty(
        name="Invert Label",
        default=True,
    )  # type: ignore

    def execute(self, context):
        label_obj = bpy.data.objects.get(self.label_obj_name)
        if not label_obj:
            self.report({"WARNING"}, "Cannot find any label layer.")
            return {'FINISHED'}

        base_layer = obj_to_layer(self.base_obj)

        label_layer = obj_to_layer(label_obj)
        label_layer.resize(base_layer.shape)
        mask = np.amax(label_layer.data, -1)
        if self.invert:
            mask = 1 - mask

        modified_layer = base_layer.copy()
        modified_layer.fill(self.fill_value, mask)
        modified_layer.name = f"{base_layer.name}_{label_layer.name}-Filled"

        self.add_layer(context, modified_layer)
        return {'FINISHED'}


class CombineLabels(bpy.types.Operator, LabelOperator):
    bl_idname = "bioxelnodes.combine_labels"
    bl_label = "Combine Labels"
    bl_description = "Combine all selected labels"

    def execute(self, context):
        label_objs = [obj for obj in context.selected_ids
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
            modified_layer.data = np.maximum(modified_layer.data, label_layer.data)
            label_names.append(label_layer.name)

        modified_layer.name = f"{'-'.join(label_names)}-Combined"

        self.add_layer(context, modified_layer)

        return {'FINISHED'}
