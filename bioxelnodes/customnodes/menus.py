import bpy
from pathlib import Path
from .nodes import AddCustomNode


class CustomNodes():
    def __init__(
        self,
        menu_items,
        nodes_file,
        class_prefix="CUSTOMNODES_MT_NODES",
        root_label='CustomNodes',
        root_icon='NONE'
    ) -> None:
        if not Path(nodes_file).is_file():
            raise FileNotFoundError(str(Path(nodes_file).resolve()))

        self.menu_items = menu_items
        self.nodes_file = str(Path(nodes_file).resolve())
        self.class_prefix = class_prefix
        self.root_label = root_label
        self.root_icon = root_icon
        self.class_prefix = class_prefix

        menu_classes = []
        self._create_menu_class(
            items=menu_items,
            label=root_label,
            menu_classes=menu_classes
        )
        self.menu_classes = menu_classes

        idname = f"{class_prefix}_{root_label.replace(' ', '').upper()}"

        def add_node_menu(self, context):
            if ('GeometryNodeTree' == bpy.context.area.spaces[0].tree_type):
                layout = self.layout
                layout.separator()
                layout.menu(idname, icon=root_icon)

        self.add_node_menu = add_node_menu

    def _create_menu_class(self, menu_classes, items, label='CustomNodes', icon=0, idname_namespace=None):
        nodes_file = self.nodes_file
        idname_namespace = idname_namespace or self.class_prefix
        idname = f"{idname_namespace}_{label.replace(' ', '').upper()}"

        # create submenu class if item is menu.
        for item in items:
            item_items = item.get('items') if item != 'separator' else None
            if item_items:
                menu_class = self._create_menu_class(
                    menu_classes=menu_classes,
                    items=item_items,
                    label=item.get('label') or 'CustomNodes',
                    icon=item.get('icon') or 0,
                    idname_namespace=idname
                )
                item['menu_class'] = menu_class

        # create menu class
        class Menu(bpy.types.Menu):
            bl_idname = idname
            bl_label = label
            nodes_file = self.nodes_file

            def draw(self, context):
                layout = self.layout

                for item in items:
                    # print(item)
                    if item == "separator":
                        layout.separator()
                    elif item.get('menu_class'):
                        layout.menu(
                            item.get('menu_class').bl_idname,
                            icon=item.get('icon') or 'NONE'
                        )
                    else:
                        op = layout.operator(
                            'customnodes.add_custom_node',
                            text=item.get('label'),
                            icon=item.get('icon') or 'NONE'
                        )
                        op.nodes_file = nodes_file
                        op.node_type = item['node_type']
                        op.node_label = item.get('label') or ""
                        op.node_description = item.get(
                            'node_description') or "Add Custom Node."
                        op.node_link = item.get('link') or True
                        op.node_callback = item.get('node_callback') or ""

        menu_classes.append(Menu)
        return Menu

    def _find_item(self, found_items, menu_items, node_type: str):

        for item in menu_items:
            if item == 'separator':
                continue

            if item.get("node_type") == node_type:
                found_items.append(item)

            item_items = item.get('items')
            if item_items:
                self._find_item(found_items, item_items, node_type)

    def find_item(self, node_type: str):
        found_items = []
        self._find_item(found_items, self.menu_items, node_type)
        return found_items[0] if len(found_items) > 0 else None

    def add_node(self, node_group, node_type: str):
        item = self.find_item(node_type)
        op = AddCustomNode()
        op.nodes_file = self.nodes_file
        op.node_type = node_type
        if item:
            op.node_label = item.get('label') or ""
            op.node_link = item.get('link') or True
            op.node_callback = item.get('node_callback') or ""
        else:
            op.node_label = ""
            op.node_link = True
            op.node_callback = ""
        return op.add_node(node_group)

    def register(self):
        for cls in self.menu_classes:
            bpy.utils.register_class(cls)

        bpy.types.NODE_MT_add.append(self.add_node_menu)
        bpy.types.Scene.customnodes_node_dir = bpy.props.StringProperty(
            name="Node Directory",
            subtype='DIR_PATH',
            default="//"
        )

    def unregister(self):
        bpy.types.NODE_MT_add.remove(self.add_node_menu)
        try:
            for cls in reversed(self.menu_classes):
                bpy.utils.unregister_class(cls)

        except RuntimeError:
            pass
