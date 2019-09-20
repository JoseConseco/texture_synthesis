
'''
Copyright (C) 2019 JOSECONSCO
Created by JOSECONSCO (loosely based on 'dynamic enum' blender template and Simple Asset Manager)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from tempfile import gettempdir
import functools
import subprocess
bl_info = {
    "name": "Texture Synthesis",
    "author": "Jose Conseco",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Side Panel (N) > Tools",
    "description": "Tile Texture and other things",
    "warning": "",
    "wiki_url": "",
    "category": "Textures",
}
import bpy
import os
from pathlib import Path
from mathutils import Vector

FILE_EDIT_TIME = None
def get_addon_name():
    return __package__.split(".")[0]

def addon_name_lowercase():
    return get_addon_name().lower()

def get_addon_preferences():
    return bpy.context.preferences.addons[get_addon_name()].preferences


def check_file_exist(filePath):
    """Retuns absolute file path, and bool - file exist?"""
    abspathToFix = Path(bpy.path.abspath(filePath))  # crappy format like c:\\..\\...\\ddada.fbx
    outputPathStr = str(abspathToFix.resolve())
    if abspathToFix.is_dir():
        outputPathStr += '\\'
    return outputPathStr, os.path.isfile(outputPathStr)


class TS_PT_TextureSynthesis(bpy.types.Panel):
    bl_idname = "TS_Panel"
    bl_label = "Texture Synthesis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tools'
    bl_context = 'objectmode'

    def draw(self, context):
        layout = self.layout.box()
        col = layout.column(align=True)
        # row = col.row(align=True)
        text_synt = context.scene.text_synth
        col.prop(text_synt, 'input_image_path')
        col.prop(text_synt, 'gen_type')
        col.prop(text_synt, 'out_method')
        if text_synt.out_method == 'TARGET_DIR':
            col.prop(text_synt, 'out_image_path')
        layout.operator("object.run_tsynthesis")

panels = (
    TS_PT_TextureSynthesis,
)

def update_panel(self, context):
    message = "Texture Synthesis: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = get_addon_preferences().category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass

class TextureSynthPreferences(bpy.types.AddonPreferences):
    bl_idname = 'texture_synthesis'

    def check_ts_exist(self, context):
        absPath, ts_exists = check_file_exist(self.text_synth_path)
        self['text_synth_path'] = absPath
        if ts_exists and os.path.basename(absPath) == "texture-synthesis.exe":
            self.display_info = "texture-synthesis.exe found in: " + absPath
        else:
            self.display_info = "texture-synthesis.exe not found in: " + absPath

    text_synth_path: bpy.props.StringProperty(name="Path to texture-synthesis.exe", description="", default="", subtype='FILE_PATH', update=check_ts_exist)
    category: bpy.props.StringProperty(name="Tab Category", description="Choose a name for the category of the panel", default="Tools", update=update_panel)
    display_info: bpy.props.StringProperty(name="Info", description="", default="")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "category", text="")
        col.prop(self, "text_synth_path", text="")
        col.label(text=self.display_info)


def check_file_was_generated(out_path):
    global FILE_EDIT_TIME
    print(f'Waiting for file {out_path} to be ready to load')
    if FILE_EDIT_TIME is None:
        if os.path.isfile(out_path):
            bpy.data.images.load(out_path, check_existing=False)
            return
    else:
        if os.path.getmtime(out_path) > FILE_EDIT_TIME:
            bpy.data.images.load(out_path, check_existing=False)
            return
    return 0.5 #else wait another 0.5 sec

class OBJECT_OT_TextureSynthesis(bpy.types.Operator):
    bl_idname = "object.run_tsynthesis"
    bl_label = "Run Texture Shynth"
    bl_description = "Generate Texture Shynth image gneration"
    bl_options = {'REGISTER'}

    @staticmethod
    def get_output_path(context):
        text_synt = context.scene.text_synth
        in_name = os.path.split(text_synt.input_image_path)[1][:-4]
        if text_synt.out_method == 'TARGET_DIR':
            # os.path.dirname()
            out_path = os.path.join(os.path.realpath(text_synt.out_image_path), in_name+'.png')
        elif text_synt.out_method == 'OVERRIDE':
            out_path = text_synt.input_image_path
        elif text_synt.out_method == 'LOAD':
            tmp = os.path.join(gettempdir(), 'text_synth')
            os.makedirs(tmp)
            out_path = os.path.join(tmp, in_name+'.png')
        return out_path


    def execute(self, context):
        text_synt = context.scene.text_synth
        out_path = self.get_output_path(context)
        command = [get_addon_preferences().text_synth_path,
                   "--out", out_path,
                   text_synt.gen_type,
                   'generate',
                   text_synt.input_image_path  # "--in",
                   ]  # warning this is sys.args[8], but order may change depending on above lines
        print(command)
        subprocess.Popen(command)
        global FILE_EDIT_TIME #we will wait till file is generated 
        if os.path.isfile(out_path):
            FILE_EDIT_TIME = os.path.getmtime(out_path)
        else:
            FILE_EDIT_TIME = None
        bpy.app.timers.register(functools.partial(check_file_was_generated, out_path), first_interval=0.5) 
        return {'FINISHED'}


class TextSynth_Settings(bpy.types.PropertyGroup):
    input_image_path: bpy.props.StringProperty(name="Input image", description="", default="", subtype='FILE_PATH')
    out_image_path: bpy.props.StringProperty(name="Output Dir", description="", default="", subtype='DIR_PATH')
    gen_type: bpy.props.EnumProperty(name='generate type',
        items=[(' ', 'generate', 'Description...'),
            ('transfer', 'transfer-style', 'Description...'),
            ('--tiling', 'tiling', 'Description...')], default=' ')
    out_method: bpy.props.EnumProperty(name='Output method', description='How / where to save generated image',
        items=[
            ('TARGET_DIR', 'To target dir', 'Write to target dir'),
            ('OVERRIDE', 'Override input image', 'Override input image'),
            ('LOAD', 'To image data', 'Load result directly to blender image data')
        ], default='TARGET_DIR')

def register():
    bpy.utils.register_class(TextureSynthPreferences)
    bpy.utils.register_class(TS_PT_TextureSynthesis)
    bpy.utils.register_class(TextSynth_Settings)
    bpy.utils.register_class(OBJECT_OT_TextureSynthesis)
    bpy.types.Scene.text_synth = bpy.props.PointerProperty(type=TextSynth_Settings)


def unregister():
    bpy.utils.unregister_class(TextureSynthPreferences)
    bpy.utils.unregister_class(TS_PT_TextureSynthesis)
    bpy.utils.unregister_class(TextSynth_Settings)
    bpy.utils.unregister_class(OBJECT_OT_TextureSynthesis)
    del bpy.types.Scene.text_synth


if __name__ == "__main__":
    register()
