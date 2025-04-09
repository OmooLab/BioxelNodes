from pathlib import Path
import shutil
import subprocess
import sys
from dataclasses import dataclass
import tomlkit


@dataclass
class Platform:
    pypi_suffix: str
    blender_tag: str


required_packages = ["SimpleITK==2.3.1",
                     "pyometiff==1.0.0",
                     "mrcfile==1.5.1",
                     "h5py==3.11.0",
                     "transforms3d==0.4.2",
                     "tifffile==2024.7.24"]


platforms = {"windows-x64": Platform(pypi_suffix="win_amd64",
                                     blender_tag="windows-x64"),
             "linux-x64": Platform(pypi_suffix="manylinux2014_x86_64",
                                   blender_tag="linux-x64"),
             "macos-arm64": Platform(pypi_suffix="macosx_12_0_arm64",
                                     blender_tag="macos-arm64"),
             "macos-x64": Platform(pypi_suffix="macosx_10_16_x86_64",
                                   blender_tag="macos-x64")}

packages_to_remove = {
    "imagecodecs",
    "numpy"
}


def run_python(args: str):
    python = Path(sys.executable).resolve()
    subprocess.run([python] + args.split(" "))


def build_extension(platform: Platform, python_version="3.11") -> None:
    wheel_dirpath = Path("./src/bioxelnodes/wheels")
    toml_filepath = Path("./src/bioxelnodes/blender_manifest.toml")
    scipy_ndimage_dirpath = Path("./scipy_ndimage", platform.blender_tag)

    # download required_packages
    run_python(
        f"-m pip download {' '.join(required_packages)} --dest {wheel_dirpath.as_posix()} --only-binary=:all: --python-version={python_version} --platform={platform.pypi_suffix}"
    )

    for f in wheel_dirpath.glob('*.whl'):
        if any([package in f.name for package in packages_to_remove]):
            f.unlink(missing_ok=True)

        elif platform.blender_tag == "macos-arm64" and \
                "lxml" in f.name and "universal2" in f.name:
            f.rename(Path(f.parent,
                          f.name.replace("universal2", "arm64")))

    for ndimage_filepath in scipy_ndimage_dirpath.iterdir():
        to_filepath = Path("./src/bioxelnodes/bioxel/scipy", ndimage_filepath.name)
        shutil.copy(ndimage_filepath, to_filepath)

    # Load the TOML file
    with toml_filepath.open("r") as file:
        manifest = tomlkit.parse(file.read())

    manifest["platforms"] = [platform.blender_tag]
    manifest["wheels"] = [f"./wheels/{f.name}"
                          for f in wheel_dirpath.glob('*.whl')]

    # build.append('generated', generated)
    # manifest.append('build', build)

    # Write the updated TOML file
    with toml_filepath.open("w") as file:
        text = tomlkit.dumps(manifest)
        file.write(text)


def main():
    platform_name = sys.argv[1]
    platform = platforms[platform_name]
    build_extension(platform)


if __name__ == "__main__":
    main()
