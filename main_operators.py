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
from .utils import get_addon_preferences
import os
import time
from pathlib import Path
from mathutils import Vector
import bpy.utils.previews
from tempfile import gettempdir
import functools
import subprocess
from . import tsynth_props

LAST_EDIT_TIME = None
COUNT_TIME = 0

def check_file_was_generated(out_path):
    global LAST_EDIT_TIME, COUNT_TIME
    current_time = time.time()
    if current_time - COUNT_TIME > 30:  # we waited 20 max seconds. Else quit timer
        COUNT_TIME = 0
        print(f'Waited 30 sec for {out_path} to be generated, no output detected. Time passed: {current_time - COUNT_TIME:.1} sec\nSkipping loading generated file')
        return
    if LAST_EDIT_TIME is None:  # dir and or did not exist. Use isFile to check img was generated
        if os.path.isfile(out_path):
            time.sleep(.300)  # just give time for file to be written?
            existing_imgs = bpy.data.images[:]
            x= bpy.data.images.load(out_path, check_existing=True)
            if x in existing_imgs:
                x.reload()
            LAST_EDIT_TIME = 0
            return
    else:
        if os.path.getmtime(out_path) > LAST_EDIT_TIME:
            time.sleep(.300)
            existing_imgs = bpy.data.images[:]
            x = bpy.data.images.load(out_path, check_existing=True)
            if x in existing_imgs:
                x.reload()
            LAST_EDIT_TIME = 0
            return
    return 1  # else wait another 0.5 sec


class TSYNTH_OT_TextureSynthesis(bpy.types.Operator):
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
    bl_label = "Run Texture Synthesis"
    bl_description = "Synthesise Texture image.\n[Shift+Click will] generate output image for all source image files in folder."
    bl_options = {'REGISTER'}

    shift_clicked = False

    def invoke(self, context, event):
        if event.shift:
            self.shift_clicked = True
        return self.execute(context)

    @staticmethod
    def get_output_path(context, out_name):
        tsynth_params = context.scene.tsynth_params
        # in_name = os.path.split(tsynth_params.input_images_dir)[1][:-4]
        if tsynth_params.out_method == 'TARGET_DIR':
            # os.path.dirname()
            out_path = os.path.join(os.path.realpath(tsynth_params.out_image_path), out_name)
        elif tsynth_params.out_method == 'OVERRIDE':
            out_path = os.path.join(tsynth_params.input_images_dir, out_name)
        elif tsynth_params.out_method == 'LOAD':
            tmp = os.path.join(gettempdir(), 'tsynth_params')
            if not os.path.isdir:
                os.makedirs(tmp)
            out_path = os.path.join(tmp, out_name)
        return out_path

    def execute(self, context):
        tsynth_params = context.scene.tsynth_params

        if tsynth_params.out_method != 'OVERRIDE' or tsynth_params.gen_type == 'multi-generate':
            out_name = tsynth_params.output_file_name
        else:  # if output override and not 'multi-generate'
            out_name = tsynth_params.my_previews[:-3]+'png'  # texture_synthesis.exe only works with png
        out_path = self.get_output_path(context, out_name)

        in_size = f"{tsynth_params.in_size_preset_x}x{tsynth_params.in_size_preset_y}" if tsynth_params.in_size_from_preset else f"{int(tsynth_params.in_size_x*tsynth_params.in_size_percent/100)}x{int(tsynth_params.in_size_y*tsynth_params.in_size_percent/100)}"
        out_size = f"{tsynth_params.out_size_preset_x}x{tsynth_params.out_size_preset_y}" if tsynth_params.out_size_from_preset else f"{int(tsynth_params.out_size_x*tsynth_params.out_size_percent/100)}x{int(tsynth_params.out_size_y*tsynth_params.out_size_percent/100)}"
        input_img_path = os.path.join(tsynth_params.input_images_dir, tsynth_params.my_previews)
        command = [get_addon_preferences().text_synth_path,
                   "--out", out_path,
                   "--out-size", out_size,
                   "--seed", str(tsynth_params.seed),
                   "--rand-init", str(tsynth_params.rand_init),
                   "--k-neighs", str(tsynth_params.k_neighs),
                   "--cauchy", str(tsynth_params.cauchy),
                   "--backtrack-pct", str(tsynth_params.backtrack_pct/100),
                   "--backtrack-stages", str(tsynth_params.backtrack_stages),
                   "--in-size", in_size]
        if tsynth_params.tiling:
            command.append('--tiling')
        # if tsynth_params.gen_type != 'generate':
        if tsynth_params.gen_type == 'generate':
            if self.shift_clicked:
                pcoll = tsynth_props.preview_collections["main"]
                for ico_name in pcoll.keys():
                    out_name = ico_name[:-3]+'png'  # texture_synthesis.exe only works with png
                    out_path = self.get_output_path(context, out_name)
                    command[2] = out_path  # change output name for each generated img
                    multi_command = command + ['generate', os.path.join(tsynth_params.input_images_dir, ico_name)]
                    print(multi_command)
                    subprocess.Popen(multi_command)
                return {'FINISHED'}

            command.extend(['generate', input_img_path])

        elif tsynth_params.gen_type == 'multi-generate':
            sel_images = [os.path.join(tsynth_params.input_images_dir, img_info.image_name) for img_info in tsynth_params.selected_imgs]
            command.extend(['generate']+sel_images)

        elif tsynth_params.gen_type == 'guided-synthesis':
            if not tsynth_params.from_guide or not tsynth_params.from_guide.has_data:
                self.report({'ERROR'}, 'From guid image is empty!. Cancelling')
                return {'CANCELLED'}
            if not tsynth_params.to_guide or not tsynth_params.to_guide.has_data:
                self.report({'ERROR'}, 'To guide image is empty!. Cancelling')
                return {'CANCELLED'}
            tsynth_params.from_guide.filepath_raw = out_path[:-4] + '_from.png'
            tsynth_params.from_guide.save()
            tsynth_params.to_guide.filepath_raw = out_path[:-4] + '_to.png'
            tsynth_params.to_guide.save()
            command.extend(['generate',
                            '--target-guide', tsynth_params.to_guide.filepath_raw,
                            '--guides', tsynth_params.from_guide.filepath_raw,
                            '--', input_img_path])  # ? or '--'+tsynth_params.input_img ?

        elif tsynth_params.gen_type == 'transfer-style':  # TODO:
            if tsynth_params.to_guide is None:
                self.report({'ERROR'}, 'To guide image is empty!. Cancelling')
                return {'CANCELLED'}
            # tsynth_params.to_guide.filepath_raw = out_path[:-4] + 'to_guide.png' #it should be loaded img....
            tsynth_params.to_guide.save()
            command[1:1] = ['--alpha', str(tsynth_params.alpha)]  # add at begning after program name
            command.extend(['transfer-style',
                            '--style', input_img_path,
                            '--guide', bpy.path.abspath(tsynth_params.to_guide.filepath_raw)])

        elif tsynth_params.gen_type == 'inpaint':
            if not tsynth_params.to_guide or not tsynth_params.to_guide.has_data:
                self.report({'ERROR'}, 'To guide image is empty!. Cancelling')
                return {'CANCELLED'}
            tsynth_params.to_guide.filepath_raw = out_path[:-4] + '_inpaint.png'
            tsynth_params.to_guide.save()
            command.extend(['--inpaint', bpy.path.abspath(tsynth_params.to_guide.filepath_raw),
                            'generate', input_img_path])

        print(command)
        subprocess.Popen(command)

        global LAST_EDIT_TIME, COUNT_TIME  # we will wait till file is generated
        if os.path.isfile(out_path):
            LAST_EDIT_TIME = os.path.getmtime(out_path)
        else:
            LAST_EDIT_TIME = None
        COUNT_TIME = time.time()
        bpy.app.timers.register(functools.partial(check_file_was_generated, out_path), first_interval=1)
        return {'FINISHED'}


class TSYNTH_OT_RefreshDir(bpy.types.Operator):
    bl_idname = "object.refresh_directory"
    bl_label = "Refresh Icons"
    bl_description = "Refresh icons from directory"
    bl_options = {"REGISTER","UNDO"}

    def execute(self, context):
        tsynth_props.FORCE_REFRESH_ICO = True
        return {"FINISHED"}
