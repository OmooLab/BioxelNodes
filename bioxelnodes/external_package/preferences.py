import bpy
from pathlib import Path
from .package import PackageInstaller, PYPI_MIRROR

# Defines the preferences panel for the addon, which shows the buttons for
# installing and reinstalling the required python packages defined in 'requirements.txt'


def get_pypi_mirrors(self, context, edit_text):
    return PYPI_MIRROR.keys()


class ExternalPackagePreferences():
    requirements_dir: bpy.props.StringProperty(
        name="requirements.txt Directory",
        subtype='DIR_PATH',
        default=Path(__file__).parent.as_posix()
    )  # type: ignore

    log_dir: bpy.props.StringProperty(
        name="Python Log Directory",
        subtype='DIR_PATH',
        default=Path(Path.home(), '.externalpackage', 'logs').as_posix()
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
        layout.label(text="Install the required packages.")

        col_main = layout.column(heading='', align=False)
        row_import = col_main.row()
        row_import.prop(self, 'pypi_mirror_provider', text='Set PyPI Mirror')

        
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
