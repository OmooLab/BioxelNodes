import bpy
import subprocess
from pathlib import Path
from .package import PackageInstaller, PYPI_MIRROR

# Defines the preferences panel for the addon, which shows the buttons for
# installing and reinstalling the required python packages defined in 'requirements.txt'


def get_pypi_mirrors(self, context, edit_text):
    return PYPI_MIRROR.keys()


class RebootBlender(bpy.types.Operator):
    bl_idname = "externalpackage.reboot_blender"
    bl_label = "Reboot Blender"
    bl_description = "Reboot Blender"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        context.window_manager.invoke_confirm(self, event)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        blender_launcher = Path(
            bpy.app.binary_path).parent / "blender-launcher.exe"
        subprocess.run([str(blender_launcher), "-con", "--python-expr",
                       "import bpy; bpy.ops.wm.recover_last_session()"])
        bpy.ops.wm.quit_blender()
        return {'FINISHED'}


class ExternalPackagePreferences():
    requirements_dir: bpy.props.StringProperty(
        name="requirements.txt Directory",
        subtype='DIR_PATH',
        default=str(Path(__file__).parent)
    )  # type: ignore

    log_dir: bpy.props.StringProperty(
        name="Python Log Directory",
        subtype='DIR_PATH',
        default=str(Path(Path.home(), '.externalpackage', 'logs'))
    )  # type: ignore

    pypi_mirror_provider: bpy.props.StringProperty(
        name='pypi_mirror_provider',
        description='PyPI Mirror Provider',
        options={'TEXTEDIT_UPDATE', 'LIBRARY_EDITABLE'},
        default='Default',
        subtype='NONE',
        search=get_pypi_mirrors,
    )  # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(
            text='**Install the required packages, then hit "Reboot Blender"**')

        col_main = layout.column(heading='', align=False)
        row_import = col_main.row()
        row_import.prop(self, 'pypi_mirror_provider', text='PyPI Mirror')

        installer = PackageInstaller(
            pypi_mirror_provider=self.pypi_mirror_provider,
            log_dir=self.log_dir,
            requirements_dir=self.requirements_dir
        )

        for package in installer.packages.values():

            name = package.get('name')
            version = package.get('version')
            description = package.get('description')

            if installer.is_installed(name):
                row = layout.row()
                row.label(text=f"{name} version {version} is installed.")
                op = row.operator('externalpackage.install_package',
                                  text=f'Reinstall {name}')
                op.package = name
                op.version = version
                op.description = f'Reinstall {name}'
            else:
                row = layout.row(heading=f"Package: {name}")
                col = row.column()
                col.label(text=str(description))
                col = row.column()
                op = col.operator('externalpackage.install_package',
                                  text=f'Install {name}')
                op.package = name
                op.version = version
                op.description = f'Install required python package: {name}'

        layout.operator(RebootBlender.bl_idname)
