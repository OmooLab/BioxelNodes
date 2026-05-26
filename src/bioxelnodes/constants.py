from pathlib import Path

NODE_LIB_FILENAME = "O_Bioxel_Nodes.blend"

NODE_LIB_DIRPATH = Path(Path(__file__).parent,
                        "assets/O_Bioxel").resolve()

LATEST_NODE_LIB_PATH = Path(NODE_LIB_DIRPATH,
                            NODE_LIB_FILENAME).resolve()

PREVIEW_COLLECTIONS = {}
