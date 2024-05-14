import bpy
from pathlib import Path
from .externalpackage import ExternalPackagePreferences


class BioxelNodesPreferences(bpy.types.AddonPreferences, ExternalPackagePreferences):
    bl_idname = __package__

    cache_dir: bpy.props.StringProperty(
        name="Set Cache Directory",
        subtype='DIR_PATH',
        default=str(Path(Path.home(), '.bioxelnodes'))
    )  # type: ignore

    do_add_segmentnode: bpy.props.BoolProperty(
        name="Add Segment Node",
        default=True,
    )  # type: ignore

    do_change_render_setting: bpy.props.BoolProperty(
        name="Change Render Setting",
        default=True,
    )  # type: ignore

    def draw(self, context):
        layout = self.layout

        # ExternalPackagePreferences Config
        self.requirements_dir = str(Path(__file__).parent)
        super().draw(context)

        layout.label(text="Configuration")
        layout.prop(self, 'cache_dir')

        layout.prop(self, "do_change_render_setting")
        layout.prop(self, "do_add_segmentnode")
