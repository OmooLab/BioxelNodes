import bpy
from .operators.node import AddNode


class NodeMenu():
    def __init__(
        self,
        menu_items,
    ) -> None:

        self.menu_items = menu_items
        self.class_prefix = f"BIOXELNODES_MT"
        root_label = "Bioxel Nodes"
        menu_classes = []
        self._create_menu_class(
            items=menu_items,
            label=root_label,
            menu_classes=menu_classes
        )
        self.menu_classes = menu_classes

        idname = f"{self.class_prefix}_{root_label.replace(' ', '').upper()}"
        icon = "FILE_VOLUME"

        def drew_menu(self, context):
            if (bpy.context.area.spaces[0].tree_type == 'GeometryNodeTree'):
                layout = self.layout
                layout.separator()
                layout.menu(idname,
                            icon=icon)
        self.drew_menu = drew_menu

    def _create_menu_class(self, menu_classes, items, label='CustomNodes', icon=0, idname_namespace=None):
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

            def draw(self, context):
                layout = self.layout
                for item in items:
                    if item == "separator":
                        layout.separator()
                    elif item.get('menu_class'):
                        layout.menu(
                            item.get('menu_class').bl_idname,
                            icon=item.get('icon') or 'NONE'
                        )
                    else:
                        op = layout.operator(
                            AddNode.bl_idname,
                            text=item.get('label'),
                            icon=item.get('icon') or 'NONE'
                        )
                        op.node_name = item['name']
                        op.node_label = item.get('label') or ""
                        op.node_description = item.get(
                            'node_description') or ""

        menu_classes.append(Menu)
        return Menu

    def register(self):
        for cls in self.menu_classes:
            bpy.utils.register_class(cls)
        bpy.types.NODE_MT_add.append(self.drew_menu)

    def unregister(self):
        bpy.types.NODE_MT_add.remove(self.drew_menu)
        for cls in reversed(self.menu_classes):
            bpy.utils.unregister_class(cls)
