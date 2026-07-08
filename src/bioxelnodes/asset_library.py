import bpy
from pathlib import Path

from .constants import NODE_LIB_DIRPATH


ASSET_LIBRARY_NAME = "O Bioxel"


def _asset_library_path():
    return str(NODE_LIB_DIRPATH)


def _normalized_path(path):
    return Path(bpy.path.abspath(path)).resolve()


def _asset_libraries():
    return bpy.context.preferences.filepaths.asset_libraries


def get_bioxel_asset_library():
    lib_path = _normalized_path(_asset_library_path())

    for lib in _asset_libraries():
        try:
            if _normalized_path(lib.path) == lib_path:
                return lib
        except Exception:
            continue

    return None


def has_bioxel_asset_library():
    return get_bioxel_asset_library() is not None


def add_bioxel_asset_library():
    if not NODE_LIB_DIRPATH.exists():
        raise FileNotFoundError(f"Node library path does not exist: {NODE_LIB_DIRPATH}")

    prefs = _asset_libraries()
    lib = get_bioxel_asset_library()

    if lib is None:
        for item in prefs:
            try:
                if item.name == ASSET_LIBRARY_NAME:
                    lib = item
                    break
            except Exception:
                continue

    if lib is None:
        lib = prefs.new()

    lib.name = ASSET_LIBRARY_NAME
    lib.path = _asset_library_path()
    lib.import_method = "PACK"
    return lib


def remove_bioxel_asset_library_if_exists():
    lib_path = _normalized_path(_asset_library_path())
    prefs = _asset_libraries()

    for lib in list(prefs):
        try:
            if "Bioxel" in lib.name or _normalized_path(lib.path) == lib_path:
                prefs.remove(lib)
        except Exception:
            continue
