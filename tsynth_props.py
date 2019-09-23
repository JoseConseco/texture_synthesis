
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

import bpy
import os
from . import get_image_size
from tempfile import gettempdir
from . import tsynth_ui

preview_collections = {}
FORCE_REFRESH_ICO = False

class SelectedImages(bpy.types.PropertyGroup):
    image_name: bpy.props.StringProperty()

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
        if os.path.exists(abs_p):
            try:
                f = open(abs_p+'write_test.txt', "w+")
            except OSError as e:
                print(e)
                self['out_image_path'] = str(gettempdir())
                tsynth_ui.MESSAGE = f'No permission to write to:  {abs_p}. Select different folder'
            else:
                tsynth_ui.MESSAGE = None
                f.close()
                os.remove(abs_p+'write_test.txt')
                self['out_image_path'] = abs_p
        else:
            self['out_image_path'] = str(gettempdir())

    def limited_previews_from_directory_items(self, context):
        ''' Dam blender limit enum to 32 max items, with ENUM_FLAG '''
        items = self.enum_previews_from_directory_items(context)
        # for i,item in enumerate(items):
        #     item[4] = i**2  # has to be power of 2 for ENUM_FLAG
        return items[:32]

    def enum_previews_from_directory_items(self, context):
        """EnumProperty callback"""
        global FORCE_REFRESH_ICO
        enum_items = []
        if context is None:
            return enum_items

        tsynth_params = context.scene.tsynth_params
        directory = tsynth_params.input_images_dir

        # Get the preview collection (defined in register func).
        pcoll = preview_collections["main"]

        if directory == pcoll.input_images_dir:
            if not FORCE_REFRESH_ICO:
                return pcoll.my_previews
            else:
                FORCE_REFRESH_ICO = False


        # bpy.ops.object.clear_img_synth()
        pcoll.clear()
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
                short_name = name[:10]+'..' + name[-5:] if len(name) > 20 else name
                enum_items.append((name, short_name, "", thumb.icon_id, i)) 

        pcoll.my_previews = enum_items
        pcoll.input_images_dir = directory
        return pcoll.my_previews

    def suffix_fix(self, context):
        file_name, ext = os.path.splitext(self.output_file_name)
        self['output_file_name'] = file_name+'.png'
    
    def in_dir_up(self,context):
        bpy.ops.object.clear_img_synth()

    def active_img_up(self,context):
        self.my_previews = self.selected_imgs[self.active_img].image_name

    input_images_dir: bpy.props.StringProperty(name="Dir:", description="Input images directory for texture synthesis", default="", subtype='DIR_PATH', update=in_dir_up)
    my_previews: bpy.props.EnumProperty(items=enum_previews_from_directory_items, name='Input Image', update=update_input_img_size)

    # my_previews_multi: bpy.props.EnumProperty(items=limited_previews_from_directory_items, name='Input Image', description='Max 32 icons. This is how blender rolls', options={'ENUM_FLAG'})
    selected_imgs: bpy.props.CollectionProperty(type=SelectedImages)
    active_img: bpy.props.IntProperty(name='active_img', description='', default=1, update=active_img_up)

    out_image_path: bpy.props.StringProperty(name="Dir", description="", default=gettempdir(), subtype='DIR_PATH', update=set_abs_path)
    gen_type: bpy.props.EnumProperty(name='Synthesise',
                                     items=[('generate', 'Simple Generate', 'Generate similar-looking images from a single example'),
                                            ('multi-generate', 'Multi Generate', 'We can also provide multiple example images and the algorithm will "remix" them into a new image.'),
                                            ('guided-synthesis', 'Guided Synthesis', 'We can also guide the generation by providing a transformation "FROM"-"TO" in a form of guide maps'),
                                            ('transfer-style', 'Style Transfer', 'Texture synthesis API supports auto-generation of example guide maps, which produces a style transfer-like effect.'),
                                            ('inpaint', 'Inpaint', 'We can also fill-in missing information with inpaint. By changing the seed, we will get different version of the "fillment".'),
                                            ], default='generate')
    tiling: bpy.props.BoolProperty(name='Tiling', description='Enables tiling of the output image', default=True)
    seed: bpy.props.IntProperty(name='seed', description='A seed value for the random generator to give pseudo-deterministic result.'
                                ' Smaller details will be different from generation to generation due to the non-deterministic nature of multi-threading', default=1, min=1)
    rand_init: bpy.props.IntProperty(name='rand init', description='The number of randomly initialized pixels before the main resolve loop starts', default=1, min=1)
    k_neighs: bpy.props.IntProperty(
        name='k-neighs', description='The number of neighboring pixels each pixel is aware of during the generation, larger numbers means more global structures are captured. Default=50', default=50, soft_max=100)
    cauchy: bpy.props.FloatProperty(name='Cauchy', description='The distribution dispersion used for picking '
                                    'best candidate (controls the distribution "tail flatness").Values close to 0.0 will produce "harsh" borders between generated "chunks".'
                                    ' Values closer to 1.0 will produce a smoother gradient on those borders', min=0, max=1, default=1.0)
    backtrack_stages: bpy.props.IntProperty(name='Backtrack stages', description='The number of backtracking stages. Backtracking prevents "garbage" generation', default=5, min=0, max=10)
    backtrack_pct: bpy.props.IntProperty(name='Backtrack %', description='The percentage of pixels to be backtracked during each p_stage.', default=50, min=0, max=100)
    output_file_name: bpy.props.StringProperty(name='Name', default='Generated.png', update=suffix_fix)

    to_guide: bpy.props.PointerProperty(name='To', type=bpy.types.Image, update=update_input_img_size)
    from_guide: bpy.props.PointerProperty(name='From', type=bpy.types.Image)

    alpha: bpy.props.FloatProperty(
        name='Guide Importance', description='Alpha parameter controls the \'importance\' of the user guide maps. If you want to preserve more details from the example map, make sure the number < 1.0. Range (0.0 - 1.0)', default=0.8, min=0.0, soft_max=1.0)

    in_size_from_preset: bpy.props.BoolProperty(name='Input Size from preset', description='Input Size from preset', default=False)
    in_size_percent: bpy.props.IntProperty(name='%', description='Input size multiplier', default=100, min=0, soft_max=100, subtype='PERCENTAGE')
    in_size_x: bpy.props.IntProperty(name='Input x', default=400)
    in_size_y: bpy.props.IntProperty(name='Input y', default=400)
    in_size_preset_x: bpy.props.EnumProperty(name='Input', description='Input size from Preset',  # can be  x * x , or x * y
                                             items=[('64',   '64', ''),
                                                    ('128', '128', ''),
                                                    ('256', '256', ''),
                                                    ('512', '512', ''),
                                                    ('1024', '1024', '')
                                                    ], default='512')
    in_size_preset_y: bpy.props.EnumProperty(name='Input', description='Input size from Preset',  # can be  x * x , or x * y
                                             items=[('64',   '64', ''),
                                                    ('128', '128', ''),
                                                    ('256', '256', ''),
                                                    ('512', '512', ''),
                                                    ('1024', '1024', '')
                                                    ], default='512')

    out_size_from_preset: bpy.props.BoolProperty(name='Output', description='Output Size from preset', default=False)
    out_size_percent: bpy.props.IntProperty(name='%', description='Output size multiplier', default=100, min=0, soft_max=100, subtype='PERCENTAGE')
    out_size_x: bpy.props.IntProperty(name='Output x', default=400)
    out_size_y: bpy.props.IntProperty(name='Output y', default=400)
    out_size_preset_x: bpy.props.EnumProperty(name='Output Size', description='From Preset',  # can be  x * x , or x * y
                                              items=[('64',   '64', ''),
                                                     ('128', '128', ''),
                                                     ('256', '256', ''),
                                                     ('512', '512', ''),
                                                     ('1024', '1024', '')
                                                     ], default='512')
    out_size_preset_y: bpy.props.EnumProperty(name='Output Size', description='From Preset',  # can be  x * x , or x * y
                                              items=[('64',   '64', ''),
                                                     ('128', '128', ''),
                                                     ('256', '256', ''),
                                                     ('512', '512', ''),
                                                     ('1024', '1024', '')
                                                     ], default='512')

    out_method: bpy.props.EnumProperty(name='Method', description='How / where to save generated image',
                                       items=[('TARGET_DIR', 'To Directory', 'Write to target dir'),
                                              ('OVERRIDE', 'Override input image', 'Override input image'),
                                              ('LOAD', 'To image data', 'Generate image to temp folder and load result to blender')
                                              ], default='TARGET_DIR')



def register_thumbs():
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


def unregister_thumbs():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
