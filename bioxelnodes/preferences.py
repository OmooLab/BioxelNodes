import bpy
from pathlib import Path
from .externalpackage import ExternalPackagePreferences


class BioxelNodesPreferences(bpy.types.AddonPreferences, ExternalPackagePreferences):
    bl_idname = __package__

    cache_dir: bpy.props.StringProperty(
        name="VDB Cache Directory",
        subtype='DIR_PATH',
        default=str(Path(Path.home(), '.bioxelnodes'))
    )  # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Configuration")
        layout.prop(self, 'cache_dir', text='Set Cache Directory')

        # ExternalPackagePreferences Config
        self.requirements_dir = str(Path(__file__).parent)
        super().draw(context)
