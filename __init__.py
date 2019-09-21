
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
#TODO:  why check_file_was_generated sometimes fails to load result?
#TODO:  multi input generate..
#TODO:  wait for inpaitn fix: https://github.com/EmbarkStudios/texture-synthesis/issues/41

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

if "bpy" in locals():
    import importlib
    importlib.reload(get_image_size)
else:
    from . import get_image_size

import bpy
import os
from pathlib import Path
from mathutils import Vector
import bpy.utils.previews
from tempfile import gettempdir
import functools
import subprocess

FILE_EDIT_TIME = None
MESSAGE = None

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


def enum_previews_from_directory_items(self, context):
    """EnumProperty callback"""
    enum_items = []

    if context is None:
        return enum_items

    ts_params = context.scene.ts_params
    directory = ts_params.input_images_dir

    # Get the preview collection (defined in register func).
    pcoll = preview_collections["main"]

    if directory == pcoll.input_images_dir:
        return pcoll.my_previews

    print("Scanning directory: %s" % directory)

    if directory and os.path.exists(directory):
        # Scan the directory for png files
        image_paths = []
        for fn in os.listdir(directory):
            if fn.lower().endswith((".png", ".bmp", ".jpg")):
                image_paths.append(fn)

        for i, name in enumerate(image_paths):
            # generates a thumbnail preview for a file.
            filepath = os.path.join(directory, name)
            icon = pcoll.get(name)
            if not icon:
                thumb = pcoll.load(name, filepath, 'IMAGE')
            else:
                thumb = pcoll[name]
            enum_items.append((name, name, "", thumb.icon_id, i))

    pcoll.my_previews = enum_items
    pcoll.input_images_dir = directory
    return pcoll.my_previews

class TS_PT_TextureSynthesis(bpy.types.Panel):
    bl_idname = "TS_Panel"
    bl_label = "Texture Synthesis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tools'
    bl_context = 'objectmode'

    def draw(self, context):
        ts_params = context.scene.ts_params
        layout = self.layout.box()
        layout.prop(ts_params, 'gen_type')

        col = layout.column(align=True)
        if ts_params.gen_type == 'guided-synthesis':
            split = col.split(factor=0.14, align=True)
            split.label(text='From')
            split.template_ID(ts_params, "from_guide", new="image.new", open="image.open")

            split = col.split(factor=0.14, align=True)
            split.label(text='To')
            split.template_ID(ts_params, "to_guide", new="image.new", open="image.open")
            row = col.row(align=True)
            # row.prop(ts_params, 'from_guide')
            # row.prop(ts_params, 'to_guide')
        if ts_params.gen_type == 'transfer-style':
            row = col.row(align=True)
            row.prop(ts_params, 'alpha')

            split = col.split(factor=0.14, align=True)
            split.label(text='Guide')
            split.template_ID(ts_params, "to_guide", new="image.new", open="image.open")
            row = col.row(align=True)
        if ts_params.gen_type == 'inpaint':
            split = col.split(factor=0.14, align=True)
            split.label(text='Mask')
            split.template_ID(ts_params, "to_guide", new="image.new", open="image.open")

        col = layout.column(align=True)
        col.prop(ts_params, "input_images_dir")
        col.template_icon_view(ts_params, "my_previews", show_labels=True)

        row = col.row(align=True)
        row.prop(ts_params, "my_previews", text='')
        if ts_params.input_images_dir and ts_params.my_previews:
            img_open = row.operator("image.open", icon='IMPORT', text='').filepath = os.path.join(ts_params.input_images_dir, ts_params.my_previews)
            
        box = layout.box()
        box.label(text = 'Settings')
        box_col = box.column(align=True)
        box_col.prop(ts_params, 'tiling')
        box_col.prop(ts_params, 'seed')
        box_col.prop(ts_params, 'rand_init')
        
        col = box.column(align=True)
        row = col.row(align=True)
        if ts_params.in_size_from_preset:
            row.prop(ts_params, 'in_size_preset')
        else:
            row.prop(ts_params, 'in_size_x')
            row.prop(ts_params, 'in_size_y')
        row.prop(ts_params, 'in_size_from_preset', icon='PRESET', text='')

        row = col.row(align=True)
        if ts_params.out_size_from_preset:
            row.prop(ts_params, 'out_size_preset')
        else:
            row.prop(ts_params, 'out_size_x')
            row.prop(ts_params, 'out_size_y')
        row.prop(ts_params, 'out_size_from_preset', icon='PRESET', text='')

        col = layout.column(align=True)
        col.prop(ts_params, 'out_method')

        if ts_params.out_method == 'TARGET_DIR':
            col.prop(ts_params, 'out_image_path')
            if MESSAGE:
                col.label(text=MESSAGE)

        layout.operator("object.run_tsynthesis", icon='NODE_TEXTURE')

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

CHECK_COUNT = 0
def check_file_was_generated(out_path):
    global FILE_EDIT_TIME, CHECK_COUNT
    CHECK_COUNT += 1
    if CHECK_COUNT > 20: #we waited 20 seconds. Skip listening for changes
        CHECK_COUNT = 0
        return
    print(f'Waiting for file {out_path} to be ready to load. CHECK_COUNT = {CHECK_COUNT}')
    if FILE_EDIT_TIME is None: #dir and or did not exist. Use isFile to check img was generated
        if os.path.isfile(out_path):
            bpy.data.images.load(out_path, check_existing=True)
            CHECK_COUNT = 0
            return
    else:
        if os.path.getmtime(out_path) > FILE_EDIT_TIME:
            bpy.data.images.load(out_path, check_existing=True)
            CHECK_COUNT = 0
            return
    return 1 #else wait another 0.5 sec

class OBJECT_OT_TextureSynthesis(bpy.types.Operator):
    '''
    1. Single example generation:
        ts.exe --out out/01.jpg generate imgs/1.jpg

    2. Multi example generation:
        ts.exe --rand-init 10 --seed 211 --in-size 300x300 -o out/02.png --debug-out-dir out generate imgs/multiexample/1.jpg imgs/multiexample/2.jpg imgs/multiexample/3.jpg imgs/multiexample/4.jpg

    3. Guided Synthesis
        ts.exe -o out/03.png generate --target-guide imgs/masks/2_target.jpg --guides imgs/masks/2_example.jpg -- imgs/2.jpg

    4. Style Transfer:
        ts.exe --alpha 0.8 -o out/04.png transfer-style --style imgs/multiexample/4.jpg --guide imgs/tom.jpg

    5. Inpaint:
        ts.exe --out-size 400 --inpaint imgs/masks/3_inpaint.jpg -o out/05.png generate imgs/3.jpg

    6. Tiling texture:
        ts.exe --inpaint imgs/masks/1_tile.jpg --out-size 400 --tiling -o out/06.bmp generate imgs/1.jpg

    7. Combining texture synthesis 'verbs':

    '''
    bl_idname = "object.run_tsynthesis"
    bl_label = "Run Texture Shynthesis"
    bl_description = "Generate Texture Shynth image gneration"
    bl_options = {'REGISTER'}

    @staticmethod
    def get_output_path(context):
        ts_params = context.scene.ts_params
        # in_name = os.path.split(ts_params.input_images_dir)[1][:-4]
        out_name = ts_params.my_previews[:-3]+'png' #texture_synthesis.exe only works with png
        if ts_params.out_method == 'TARGET_DIR':
            # os.path.dirname()
            out_path = os.path.join(os.path.realpath(ts_params.out_image_path), out_name)
        elif ts_params.out_method == 'OVERRIDE':
            out_path = os.path.join(ts_params.input_images_dir, out_name)
        elif ts_params.out_method == 'LOAD':
            tmp = os.path.join(gettempdir(), 'ts_params')
            if not os.path.isdir:
                os.makedirs(tmp)
            out_path = os.path.join(tmp, out_name)
        return out_path

    def execute(self, context):
        ts_params = context.scene.ts_params
        out_path = self.get_output_path(context)

        in_size = ts_params.in_size_preset if ts_params.in_size_from_preset else f"{ts_params.in_size_x}x{ts_params.in_size_y}"
        out_size = ts_params.out_size_preset if ts_params.out_size_from_preset else f"{ts_params.out_size_x}x{ts_params.out_size_y}"
        input_img_path = os.path.join(ts_params.input_images_dir, ts_params.my_previews)
        command = [get_addon_preferences().text_synth_path,
                   "--out", out_path,
                   "--out-size", out_size,
                   "--seed", str(ts_params.seed),
                   "--rand-init", str(ts_params.rand_init),
                   "--in-size", in_size]
        if ts_params.tiling:
            command.append('--tiling')
        # if ts_params.gen_type != 'generate':
        if ts_params.gen_type == 'generate':
            command.extend(['generate', input_img_path]) 
            
        elif ts_params.gen_type == 'multi-generate':  #TODO:
            command.extend(['generate', input_img_path]) 

        elif ts_params.gen_type == 'guided-synthesis': 
            if not ts_params.from_guide or not ts_params.from_guide.has_data:
                self.report({'ERROR'}, 'From guid image is empty!. Cancelling')
                return {'CANCELLED'}
            if not ts_params.to_guide or not ts_params.to_guide.has_data:
                self.report({'ERROR'}, 'To guide image is empty!. Cancelling')
                return {'CANCELLED'}
            ts_params.from_guide.filepath_raw = out_path[:-4] + '_from.png'
            ts_params.from_guide.save()
            ts_params.to_guide.filepath_raw = out_path[:-4] + '_to.png'
            ts_params.to_guide.save()
            command.extend(['generate',
                            '--target-guide', ts_params.to_guide.filepath_raw,
                            '--guides', ts_params.from_guide.filepath_raw,
                            '--',input_img_path]) #? or '--'+ts_params.input_img ?

        elif ts_params.gen_type == 'transfer-style':  # TODO:
            if not ts_params.to_guide or not ts_params.to_guide.has_data:
                self.report({'ERROR'}, 'To guide image is empty!. Cancelling')
                return {'CANCELLED'}
            # ts_params.to_guide.filepath_raw = out_path[:-4] + 'to_guide.png' #it should be loaded img....
            ts_params.to_guide.save()
            command[1:1] =['--alpha', str(ts_params.alpha)] #add at begning after program name
            command.extend(['transfer-style',
                            '--style', input_img_path,
                            '--guide', bpy.path.abspath(ts_params.to_guide.filepath_raw)])

        elif ts_params.gen_type == 'inpaint': 
            if not ts_params.to_guide or not ts_params.to_guide.has_data:
                self.report({'ERROR'}, 'To guide image is empty!. Cancelling')
                return {'CANCELLED'}
            ts_params.to_guide.filepath_raw = out_path[:-4] + '_inpaint.png'
            ts_params.to_guide.save()
            command.extend(['--inpaint', bpy.path.abspath(ts_params.to_guide.filepath_raw), 
                            'generate', input_img_path])

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
    def update_input_img_size(self, context):
        input_img_path = os.path.join(self.input_images_dir, self.my_previews) if self.gen_type != 'transfer-style' else bpy.path.abspath(self.to_guide.filepath_raw)
        try:
            width, height = get_image_size.get_image_size(input_img_path)
        except get_image_size.UnknownImageFormat:
            width, height = 400, 400
        print(f'Updating output size {width}x{height}')
        self['in_size_x'], self['in_size_y'] = width, height
        self['out_size_x'], self['out_size_y'] = width, height

    def set_abs_path(self, context):
        abs_p = bpy.path.abspath(self['out_image_path'])
        global MESSAGE
        if os.path.exists(abs_p):
            try:
                f = open(abs_p+'write_test.txt', "w+")
            except OSError as e:
                print(e)
                self['out_image_path'] = str(gettempdir())
                MESSAGE = f'No permission to write to:  {abs_p}. Select different folder'
            else:
                MESSAGE = None
                f.close()
                os.remove(abs_p+'write_test.txt')
                self['out_image_path'] = abs_p
        else:
            self['out_image_path'] = str(gettempdir())
            
    input_images_dir: bpy.props.StringProperty(name="Images", description="Input images directory for texture synthesis", default="", subtype='DIR_PATH')
    my_previews: bpy.props.EnumProperty(items=enum_previews_from_directory_items, name='Input Image', update=update_input_img_size)

    out_image_path: bpy.props.StringProperty(name="Output Dir", description="", default=gettempdir(), subtype='DIR_PATH', update=set_abs_path)
    gen_type: bpy.props.EnumProperty(name='Synthesise',
                    items=[('generate', 'Simple Generate', 'Generate similar-looking images from a single example'),
                           ('multi-generate', 'Multi Generate', 'We can also provide multiple example images and the algorithm will "remix" them into a new image.'),
                           ('guided-synthesis', 'Guided Synthesis', 'We can also guide the generation by providing a transformation "FROM"-"TO" in a form of guide maps'),
                           ('transfer-style', 'Style Transfer', 'Texture synthesis API supports auto-generation of example guide maps, which produces a style transfer-like effect.'),
                           ('inpaint', 'Inpaint', 'We can also fill-in missing information with inpaint. By changing the seed, we will get different version of the "fillment".'),
                           ], default='generate')
    tiling: bpy.props.BoolProperty(name='Tiling', description='Enables tiling of the output image', default=True)
    seed: bpy.props.IntProperty(name='seed', description='A seed value for the random generator to give pseudo-deterministic result. Smaller details will be different from generation to generation due to the non-deterministic nature of multi-threading', default=1)
    rand_init: bpy.props.IntProperty(name='rand init', description='The number of randomly initialized pixels before the main resolve loop starts', default=1)

    to_guide: bpy.props.PointerProperty(name='To', type=bpy.types.Image, update=update_input_img_size)
    from_guide: bpy.props.PointerProperty(name='From', type=bpy.types.Image)

    alpha: bpy.props.FloatProperty(
        name='Guide Importance', description='Alpha parameter controls the \'importance\' of the user guide maps. If you want to preserve more details from the example map, make sure the number < 1.0. Range (0.0 - 1.0)', default=0.8, min=0.0, soft_max=1.0)

    in_size_from_preset: bpy.props.BoolProperty(name='Input Size from preset', description='Input Size from preset', default=True)
    in_size_x: bpy.props.IntProperty(name='input size x', default=400)
    in_size_y: bpy.props.IntProperty(name='input size y', default=400)
    in_size_preset: bpy.props.EnumProperty(name='Input Size', description='From Preset', #can be  x * x , or x * y
                                           items=[('64x64',   '64x64', ''),
                                                  ('128x128', '128x128', ''),
                                                  ('256x256', '256x256', ''),
                                                  ('512x512', '512x512', ''),
                                                  ('1024x1024', '1024x1024', '')
                                                  ], default='512x512')
    
    out_size_from_preset: bpy.props.BoolProperty(name='Output Size from preset', description='Output Size from preset', default=True)
    out_size_x: bpy.props.IntProperty(name='Output size x', default=400)
    out_size_y: bpy.props.IntProperty(name='Output size y', default=400)
    out_size_preset: bpy.props.EnumProperty(name='Output Size', description='From Preset',  # can be  x * x , or x * y
                                            items=[('64x64',   '64x64', ''),
                                                   ('128x128', '128x128', ''),
                                                   ('256x256', '256x256', ''),
                                                   ('512x512', '512x512', ''),
                                                   ('1024x1024', '1024x1024', '')
                                                   ], default='512x512')

    out_method: bpy.props.EnumProperty(name='Output method', description='How / where to save generated image',
                                       items=[('TARGET_DIR', 'To Directory', 'Write to target dir'),
                                              ('OVERRIDE', 'Override input image', 'Override input image'),
                                              ('LOAD', 'To image data', 'Load result directly to blender image data')
                                              ], default='TARGET_DIR')


# We can store multiple preview collections here,
# however in this example we only store "main"
preview_collections = {}

def register():
    bpy.utils.register_class(TextureSynthPreferences)
    bpy.utils.register_class(TS_PT_TextureSynthesis)
    bpy.utils.register_class(TextSynth_Settings)
    bpy.utils.register_class(OBJECT_OT_TextureSynthesis)
    bpy.types.Scene.ts_params = bpy.props.PointerProperty(type=TextSynth_Settings)

    # Note that preview collections returned by bpy.utils.previews
    # are regular Python objects - you can use them to store custom data.
    #
    # This is especially useful here, since:
    # - It avoids us regenerating the whole enum over and over.
    # - It can store enum_items' strings
    #   (remember you have to keep those strings somewhere in py,
    #   else they get freed and Blender references invalid memory!).
    
    pcoll = bpy.utils.previews.new()
    pcoll.input_images_dir = ""
    pcoll.my_previews = ()

    preview_collections["main"] = pcoll



def unregister():
    bpy.utils.unregister_class(TextureSynthPreferences)
    bpy.utils.unregister_class(TS_PT_TextureSynthesis)
    bpy.utils.unregister_class(TextSynth_Settings)
    bpy.utils.unregister_class(OBJECT_OT_TextureSynthesis)
    del bpy.context.scene.ts_params.my_previews
    del bpy.types.Scene.ts_params

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()



if __name__ == "__main__":
    register()
