import bpy
from pathlib import Path


class BioxelNodesPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cache_dir: bpy.props.StringProperty(
        name="Set Cache Directory",
        subtype='DIR_PATH',
        default=str(Path(Path.home(), '.bioxel'))
    )  # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Configuration")
        layout.prop(self, 'cache_dir')
