import bpy
from pathlib import Path

from .constants import LATEST_NODE_LIB_PATH, NODE_LIB_DIRPATH, NODE_LIB_FILENAME


ASSET_LIBRARY_NAME = "O Bioxel"
ASSET_LIBRARY_READY = "READY"
ASSET_LIBRARY_OUTDATED = "OUTDATED"
ASSET_LIBRARY_MISSING = "MISSING"

STATUS_MESSAGES = {
    "missing": "O Bioxel asset library is not installed.",
    "missing_blend": "O Bioxel node library file is missing.",
    "outdated": "O Bioxel node library needs update.",
    "ready": "O Bioxel asset library is ready.",
}


def _asset_library_path():
    return str(NODE_LIB_DIRPATH)


def _normalized_path(path):
    return Path(bpy.path.abspath(path)).resolve()


def _asset_libraries():
    return bpy.context.preferences.filepaths.asset_libraries


def _find_bioxel_asset_library():
    lib_path = _normalized_path(_asset_library_path())
    named_lib = None

    for lib in _asset_libraries():
        try:
            if _normalized_path(lib.path) == lib_path:
                return lib
            if lib.name == ASSET_LIBRARY_NAME:
                named_lib = lib
        except Exception:
            continue

    return named_lib


def _node_lib_path_for_library(lib):
    return _normalized_path(lib.path) / NODE_LIB_FILENAME


def get_bioxel_asset_library():
    lib_path = _normalized_path(_asset_library_path())

    for lib in _asset_libraries():
        try:
            if _normalized_path(lib.path) == lib_path:
                return lib
        except Exception:
            continue

    return None


def get_bioxel_asset_library_status():
    lib = _find_bioxel_asset_library()
    lib_path = _normalized_path(_asset_library_path())

    if lib is None:
        return {"code": ASSET_LIBRARY_MISSING, "reason": "missing",
                "message": STATUS_MESSAGES["missing"]}

    try:
        installed_lib_path = _normalized_path(lib.path)
    except Exception:
        return {"code": ASSET_LIBRARY_MISSING, "reason": "missing",
                "message": STATUS_MESSAGES["missing"]}

    if not _node_lib_path_for_library(lib).is_file():
        return {"code": ASSET_LIBRARY_MISSING, "reason": "missing_blend",
                "message": STATUS_MESSAGES["missing_blend"]}

    if installed_lib_path != lib_path:
        return {"code": ASSET_LIBRARY_OUTDATED, "reason": "outdated",
                "message": STATUS_MESSAGES["outdated"]}

    return {"code": ASSET_LIBRARY_READY, "reason": "ready",
            "message": STATUS_MESSAGES["ready"]}


def has_bioxel_asset_library():
    return get_bioxel_asset_library_status()["code"] in {
        ASSET_LIBRARY_READY,
        ASSET_LIBRARY_OUTDATED,
    }


def add_bioxel_asset_library():
    if not NODE_LIB_DIRPATH.exists():
        raise FileNotFoundError(f"Node library path does not exist: {NODE_LIB_DIRPATH}")
    if not LATEST_NODE_LIB_PATH.is_file():
        raise FileNotFoundError(f"Node library file does not exist: {LATEST_NODE_LIB_PATH}")

    prefs = _asset_libraries()
    lib = _find_bioxel_asset_library()

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
