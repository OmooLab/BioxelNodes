import bpy
from pathlib import Path


class BioxelNodesPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cache_dir: bpy.props.StringProperty(
        name="Set Cache Directory",
        subtype='DIR_PATH',
        default=str(Path(Path.home(), '.bioxelnodes'))
    )  # type: ignore

    change_render_setting: bpy.props.BoolProperty(
        name="Change Render Setting on First Import",
        default=True,
    )  # type: ignore

    node_import_method: bpy.props.EnumProperty(name="Node Import Method",
                                               default="LINK",
                                               items=[("LINK", "Link", ""),
                                                      ("APPEND", "Append (Reuse Data)", "")])  # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Configuration")
        layout.prop(self, 'cache_dir')
        layout.prop(self, "change_render_setting")
        layout.prop(self, "node_import_method")
