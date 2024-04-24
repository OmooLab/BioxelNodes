from pathlib import Path
import shutil
from bioxelnodes.utils import get_bioxels_obj
import bpy


class BIOXELNODES_PT_Bioxels(bpy.types.Panel):
    bl_idname = "BIOXELNODES_PT_Bioxels"
    bl_label = "Bioxels"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, 'bioxels_dir')


class SaveBioxels(bpy.types.Operator):
    bl_idname = "bioxelnodes.save_bioxels"
    bl_label = "Save Bioxels"
    bl_description = "Save Bioxels to Directory."
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        bioxels_obj = None
        for obj in bpy.context.selected_objects:
            bioxels_obj = get_bioxels_obj(obj)
            break

        return True if bioxels_obj else False

    def execute(self, context):
        bioxels_objs = []

        for obj in bpy.context.selected_objects:
            bioxels_obj = get_bioxels_obj(obj)
            if bioxels_obj:
                bioxels_objs.append(bioxels_obj)

        if len(bioxels_objs) == 0:
            self.report({"WARNING"}, "Cannot find any bioxels.")
            return {'FINISHED'}

        for bioxels_obj in bioxels_objs:
            name = bioxels_obj.parent.name

            # "//"
            bioxels_dir = bpy.path.abspath(context.scene.bioxels_dir)
            source_dir = bpy.path.abspath(bioxels_obj.data.filepath)

            output_path: Path = Path(bioxels_dir, f"{name}.vdb").resolve()
            source_path: Path = Path(source_dir).resolve()

            if output_path != source_path:
                shutil.copy(source_path, output_path)

            blend_path = Path(bpy.path.abspath("//")).resolve()
            bioxels_obj.data.filepath = bpy.path.relpath(
                str(output_path), start=str(blend_path))
            self.report({"INFO"}, f"Successfully saved to {output_path}")

        return {'FINISHED'}
