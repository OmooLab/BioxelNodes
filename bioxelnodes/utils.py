import bpy
import mathutils


def get_node_by_type(nodes, type_name: str):
    return [node for node in nodes if type(node).__name__ == type_name]


def show_message(message="", title="Message Box", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def calc_bbox_verts(origin, size):
    bbox_origin = mathutils.Vector(
        (origin[0], origin[1], origin[2]))
    bbox_size = mathutils.Vector(
        (size[0], size[1], size[2]))
    bbox_verts = [
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + 0,
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + 0,
            bbox_origin[2] + bbox_size[2]
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + 0,
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + bbox_size[2]
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + 0,
            bbox_origin[2] + 0
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + 0,
            bbox_origin[2] + bbox_size[2],
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + 0,
        ),
        (
            bbox_origin[0] + bbox_size[0],
            bbox_origin[1] + bbox_size[1],
            bbox_origin[2] + bbox_size[2],
        ),
    ]
    return bbox_verts


def get_bioxels_obj(current_obj):
    bioxels_obj = None
    if current_obj.get('bioxels_container'):
        bioxels_values = []
        for obj in bpy.data.objects:
            if obj.parent == current_obj and obj.get('bioxels'):
                bioxels_values.append(obj)

        if len(bioxels_values) > 0:
            bioxels_obj = bioxels_values[0]

    elif current_obj.get('bioxels') and current_obj.parent:
        if current_obj.parent.get('bioxels_container'):
            bioxels_obj = current_obj

    return bioxels_obj

def get_all_bioxels_objs():
    bioxels_objs = []

    for obj in bpy.data.objects:
        if obj.parent:
            if obj.parent.get('bioxels_container') and obj.get('bioxels'):
                bioxels_objs.append(obj)
    
    return list(set(bioxels_objs))

def extract_last_number(text):
    # Initialize an empty string to store the digits
    digits = ""

    # Iterate through the characters in reverse order
    started = False
    for char in text[::-1]:
        if char.isdigit():
            started = True
            # If the character is a digit, add it to the digits string
            digits += char
        else:
            if started:
                # If a non-digit character is encountered, stop the loop
                break

    # Reverse the digits string to get the correct order
    last_number = digits[::-1]

    return int(last_number)


def add_driver(target_prop, var_sources, expression):

    driver = target_prop.driver_add("default_value")
    is_vector = isinstance(driver, list)
    drivers = driver if is_vector else [driver]

    for i, driver in enumerate(drivers):
        for j, var_source in enumerate(var_sources):

            source = var_source['source']
            prop = var_source['prop']

            var = driver.driver.variables.new()
            var.name = f"var{j}"

            var.targets[0].id_type = source.id_type
            var.targets[0].id = source
            var.targets[0].data_path = f'["{prop}"][{i}]'\
                if is_vector else f'["{prop}"]'

        driver.driver.expression = expression


def add_direct_driver(target, target_prop, source, source_prop):
    target_prop = target.inputs.get(target_prop)
    drivers = [
        {
            "source": source,
            "prop": source_prop
        }
    ]
    expression = "var0"
    add_driver(target_prop, drivers, expression)
