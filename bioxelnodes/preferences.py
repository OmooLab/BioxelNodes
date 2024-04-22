import bpy
from pathlib import Path
from .externalpackage import ExternalPackagePreferences


class BioxelNodesPreferences(bpy.types.AddonPreferences, ExternalPackagePreferences):
    bl_idname = __package__

    cache_dir: bpy.props.StringProperty(
        name="Python Log Directory",
        subtype='DIR_PATH',
        default=Path(Path.home(), '.bioxelnodes').as_posix()
    )  # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="Configuration")
        layout.prop(self, 'cache_dir', text='Set Cache Directory')

        # ExternalPackagePreferences Config
        self.requirements_dir = Path(__file__).parent.as_posix()
        super().draw(context)
