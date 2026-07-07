import json
import uuid
import webbrowser
import bpy
from pathlib import Path
import shutil

from ..asset_library import add_bioxel_asset_library
from ..constants import LATEST_NODE_LIB_PATH
from ..utils import (
    get_all_layer_objs,
    get_cache_dir,
    get_node_version,
    is_missing_layer,
)


class CleanTemp(bpy.types.Operator):
    bl_idname = "bioxel.clear_temp"
    bl_label = "Clean Temp"
    bl_description = "Clean all cache in temp (include other project cache)"

    def execute(self, context):
        cache_dir = get_cache_dir()
        try:
            shutil.rmtree(cache_dir)
            self.report({"INFO"}, f"Successfully cleaned temp.")
            return {"FINISHED"}
        except:
            self.report(
                {"WARNING"}, "Fail to clean temp, you may do it manually.")
            return {"CANCELLED"}

    def invoke(self, context, event):
        context.window_manager.invoke_confirm(
            self,
            event,
            message="All temp files will be removed, include other project cache, do you still want to clean?",
        )
        return {"RUNNING_MODAL"}


class RenderSettingPreset(bpy.types.Operator):
    bl_idname = "bioxel.render_setting_preset"
    bl_label = "Render Setting Presets"
    bl_description = "Render setting presets for bioxel"
    bl_options = {"UNDO"}

    PRESETS = {
        "performance": "Performance",
        "balance": "Balance",
        "quality": "Quality",
    }

    preset: bpy.props.EnumProperty(
        name="Preset", default="balance", items=[(k, v, "") for k, v in PRESETS.items()]
    )  # type: ignore

    def execute(self, context):
        if self.preset == "performance":
            # EEVEE
            bpy.context.scene.eevee.use_taa_reprojection = False
            # bpy.context.scene.eevee.use_shadow_jitter_viewport = True
            bpy.context.scene.eevee.volumetric_tile_size = "4"
            bpy.context.scene.eevee.volumetric_shadow_samples = 32
            bpy.context.scene.eevee.volumetric_samples = 64
            bpy.context.scene.eevee.volumetric_ray_depth = 1
            bpy.context.scene.eevee.use_volumetric_shadows = True

            # Cycles
            bpy.context.scene.cycles.volume_bounces = 4
            bpy.context.scene.cycles.transparent_max_bounces = 4
            bpy.context.scene.cycles.volume_biased = True
            bpy.context.scene.cycles.volume_preview_step_rate = 100
            bpy.context.scene.cycles.volume_step_rate = 100

        elif self.preset == "balance":
            # EEVEE
            bpy.context.scene.eevee.use_taa_reprojection = False
            # bpy.context.scene.eevee.use_shadow_jitter_viewport = True
            bpy.context.scene.eevee.volumetric_tile_size = "2"
            bpy.context.scene.eevee.volumetric_shadow_samples = 64
            bpy.context.scene.eevee.volumetric_samples = 128
            bpy.context.scene.eevee.volumetric_ray_depth = 8
            bpy.context.scene.eevee.use_volumetric_shadows = True

            # Cycles
            bpy.context.scene.cycles.volume_bounces = 8
            bpy.context.scene.cycles.transparent_max_bounces = 16
            bpy.context.scene.cycles.volume_biased = True
            bpy.context.scene.cycles.volume_preview_step_rate = 10
            bpy.context.scene.cycles.volume_step_rate = 10

        elif self.preset == "quality":
            # EEVEE
            bpy.context.scene.eevee.use_taa_reprojection = False
            # bpy.context.scene.eevee.use_shadow_jitter_viewport = True
            bpy.context.scene.eevee.volumetric_tile_size = "1"
            bpy.context.scene.eevee.volumetric_shadow_samples = 128
            bpy.context.scene.eevee.volumetric_samples = 256
            bpy.context.scene.eevee.volumetric_ray_depth = 16
            bpy.context.scene.eevee.use_volumetric_shadows = True

            # Cycles
            bpy.context.scene.cycles.volume_bounces = 16
            bpy.context.scene.cycles.transparent_max_bounces = 32
            bpy.context.scene.cycles.volume_biased = False

        return {"FINISHED"}


class Help(bpy.types.Operator):
    bl_idname = "bioxel.help"
    bl_label = "Need Help?"
    bl_description = "Online Manual for Beginner"
    bl_icon = "HELP"

    def execute(self, context):
        webbrowser.open("https://docs.omoolab.xyz/bioxelnodes/latest/", new=2)

        return {"FINISHED"}


class AddAssetLibrary(bpy.types.Operator):
    bl_idname = "bioxel.add_asset_library"
    bl_label = "Add Nodes Library"
    bl_description = "Add the bundled O Bioxel asset library"

    def execute(self, context):
        try:
            add_bioxel_asset_library()
        except FileNotFoundError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "NODE_EDITOR":
                    area.tag_redraw()

        self.report({"INFO"}, "O Bioxel asset library is ready.")
        return {"FINISHED"}


# 定义虚无化切换操作
class TogglePhantom(bpy.types.Operator):
    """Toggle object phantom state (ray invisible, no shadows, semi-transparent wireframe)"""

    bl_idname = "bioxel.toggle_phantom"
    bl_label = "Toggle Phantom"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        obj = context.active_object
        if not obj:
            self.report({"WARNING"}, "No object selected")
            return {"CANCELLED"}

        # 获取3D视图空间
        view_space = None
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        view_space = space
                        break
                if view_space:
                    break

        # 确保存储状态的文本数据块存在
        text_name = "phantom_orig_states"
        if text_name not in bpy.data.texts:
            bpy.data.texts.new(text_name)

        # 从文本数据块加载状态
        states_text = bpy.data.texts[text_name]
        try:
            states = json.loads(states_text.as_string())
        except:
            states = {}

        def get_obj_uuid(obj):
            if "bioxel_uuid" not in obj:
                obj["bioxel_uuid"] = uuid.uuid4().hex
            return obj["bioxel_uuid"]

        # 使用物体的唯一标识符来追踪
        obj_uuid = get_obj_uuid(obj)

        # 检查物体是否已经处于虚无化状态
        is_phantom = (
            obj.display_type == "SOLID"
            and obj.show_wire
            and obj.show_in_front
            and round(obj.color[3], 2) == 0.10
            and not obj.visible_camera
            and not obj.visible_diffuse
            and not obj.visible_glossy
            and not obj.visible_transmission
            and not obj.visible_volume_scatter
            and not obj.visible_shadow
        )

        if is_phantom:
            # 恢复原始状态
            if obj_uuid in states:
                state = states[obj_uuid]
                obj.display_type = state["display_type"]
                obj.show_wire = state["show_wire"]
                obj.show_in_front = state["show_in_front"]
                obj.color = state["color"]
                obj.visible_camera = state["visible_camera"]
                obj.visible_diffuse = state["visible_diffuse"]
                obj.visible_glossy = state["visible_glossy"]
                obj.visible_transmission = state["visible_transmission"]
                obj.visible_volume_scatter = state["visible_volume_scatter"]
                obj.visible_shadow = state["visible_shadow"]

                # 恢复视图着色设置（如果之前有保存）
                if view_space and "viewport_color_type" in state:
                    view_space.shading.color_type = state["viewport_color_type"]

                del states[obj_uuid]
                self.report({"INFO"}, f"Object restored")
        else:
            # 保存原始状态
            state_data = {
                "display_type": obj.display_type,
                "show_wire": obj.show_wire,
                "show_in_front": obj.show_in_front,
                "color": list(obj.color),  # 保存RGBA颜色值
                "visible_camera": obj.visible_camera,
                "visible_diffuse": obj.visible_diffuse,
                "visible_glossy": obj.visible_glossy,
                "visible_transmission": obj.visible_transmission,
                "visible_volume_scatter": obj.visible_volume_scatter,
                "visible_shadow": obj.visible_shadow,
            }

            # 检查并处理视图着色设置
            if view_space:
                # 保存当前视图着色设置
                state_data["viewport_color_type"] = view_space.shading.color_type

                # 检查当前是否为object, random或attribute
                valid_types = {"OBJECT", "RANDOM", "ATTRIBUTE"}
                if view_space.shading.color_type not in valid_types:
                    # 改为object模式
                    view_space.shading.color_type = "OBJECT"

            states[obj_uuid] = state_data

            # 设置虚无化状态
            obj.display_type = "SOLID"  # 以实体方式显示
            obj.show_wire = True  # 显示线框
            obj.show_in_front = True  # 显示在其他物体前面
            # 保持RGB不变，仅修改alpha透明度为0.1
            obj.color[3] = 0.1
            # 关闭所有射线可见性和投影
            obj.visible_camera = False
            obj.visible_diffuse = False
            obj.visible_glossy = False
            obj.visible_transmission = False
            obj.visible_volume_scatter = False
            obj.visible_shadow = False
            self.report({"INFO"}, f"Object phantomed")

        # 保存状态到文本数据块
        states_text.clear()
        states_text.write(json.dumps(states, indent=2))

        return {"FINISHED"}
