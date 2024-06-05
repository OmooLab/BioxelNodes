import bpy
from pathlib import Path

class BioxelNodesPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cache_dir: bpy.props.StringProperty(
        name="Set Cache Directory",
        subtype='DIR_PATH',
        default=str(Path(Path.home(), '.bioxelnodes'))
    )  # type: ignore

    do_change_render_setting: bpy.props.BoolProperty(
        name="Change Render Setting",
        default=True,
    )  # type: ignore

    def draw(self, context):
        layout = self.layout

        layout.label(text="Configuration")
        layout.prop(self, 'cache_dir')
        layout.prop(self, "do_change_render_setting")
