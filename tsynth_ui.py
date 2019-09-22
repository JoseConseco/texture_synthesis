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
from . import tsynth_props

MESSAGE = None

class TSYNTH_PT_Previews(bpy.types.Panel):
    bl_idname = 'TSYNTH_PT_Previews'
    bl_label = 'PanelName'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_ui_units_x = 5

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.scale_y = 1.2
        col.prop(context.scene.tsynth_params, 'my_previews_multi', expand=True)


class TSYNTH_PT_TextureSynthesis(bpy.types.Panel):
    bl_idname = "TSYNTH_PT_TextureSynthesis"
    bl_label = "Texture Synthesis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tools'
    bl_context = 'objectmode'

    def draw(self, context):
        tsynth_params = context.scene.tsynth_params
        layout = self.layout.box()
        layout.prop(tsynth_params, 'gen_type')

        box = layout.box()
        box.label(text='Input Image(s)')
        col = box.column(align=True)
        if tsynth_params.gen_type == 'guided-synthesis':
            split = col.split(factor=0.14, align=True)
            split.label(text='From')
            split.template_ID(tsynth_params, "from_guide", new="image.new", open="image.open")

            split = col.split(factor=0.14, align=True)
            split.label(text='To')
            split.template_ID(tsynth_params, "to_guide", new="image.new", open="image.open")
            row = col.row(align=True)
            # row.prop(tsynth_params, 'from_guide')
            # row.prop(tsynth_params, 'to_guide')

        if tsynth_params.gen_type == 'transfer-style':
            row = col.row(align=True)
            row.prop(tsynth_params, 'alpha')

            split = col.split(factor=0.14, align=True)
            split.label(text='Guide')
            split.template_ID(tsynth_params, "to_guide", new="image.new", open="image.open")
            row = col.row(align=True)
        if tsynth_params.gen_type == 'inpaint':
            split = col.split(factor=0.14, align=True)
            split.label(text='Mask')
            split.template_ID(tsynth_params, "to_guide", new="image.new", open="image.open")

        col = box.column(align=True)
        col.prop(tsynth_params, "input_images_dir")
        if tsynth_params.gen_type == 'multi-generate':  # also multigenerate
            # col.prop(tsynth_params, 'my_previews_multi', expand=False)
            pcoll = tsynth_props.preview_collections["main"]
            row = col.row(align=True)
            for ico_name in tsynth_params.my_previews_multi:
                row.template_icon(pcoll[ico_name].icon_id, scale=4.0)
            # col.template_icon_view(tsynth_params, "my_previews_multi", show_labels=True)
            col.prop_with_popover(tsynth_params, 'my_previews', text='', panel='TSYNTH_PT_Previews')  # 'my_previews' cos it wont work with 'my_previews_multi'
        else:
            col.template_icon_view(tsynth_params, "my_previews", show_labels=True, scale=4.0, scale_popup=5.0)
            row = col.row(align=True)
            row.prop(tsynth_params, "my_previews", text='')
            if tsynth_params.input_images_dir and tsynth_params.my_previews:
                img_open = row.operator("image.open", icon='IMPORT', text='').filepath = os.path.join(tsynth_params.input_images_dir, tsynth_params.my_previews)

        box = layout.box()
        box.label(text='Settings')
        box_col = box.column(align=True)
        box_col.prop(tsynth_params, 'tiling', icon='OUTLINER_OB_LIGHTPROBE')
        box_col.prop(tsynth_params, 'seed')
        box_col.prop(tsynth_params, 'rand_init')
        box_col.prop(tsynth_params, 'k_neighs')
        box_col.prop(tsynth_params, 'cauchy')

        col = box.column(align=True)
        row = col.row(align=True)
        if tsynth_params.in_size_from_preset:
            row.prop(tsynth_params, 'in_size_preset_x')
            row.prop(tsynth_params, 'in_size_preset_y', text='')
        else:
            row.label(text='Input')
            row.prop(tsynth_params, 'in_size_x', text='x')
            row.prop(tsynth_params, 'in_size_y', text='y')
            row.prop(tsynth_params, 'in_size_percent')
        row.prop(tsynth_params, 'in_size_from_preset', icon='PRESET', text='')

        row = col.row(align=True)
        if tsynth_params.out_size_from_preset:
            row.prop(tsynth_params, 'out_size_preset_x')
            row.prop(tsynth_params, 'out_size_preset_y', text='')
        else:
            row.label(text='Output')
            row.prop(tsynth_params, 'out_size_x', text='x')
            row.prop(tsynth_params, 'out_size_y', text='y')
            row.prop(tsynth_params, 'out_size_percent')
        row.prop(tsynth_params, 'out_size_from_preset', icon='PRESET', text='')

        box = layout.box()
        box.label(text='Output')
        col = box.column(align=True)
        col.prop(tsynth_params, 'out_method')

        if tsynth_params.out_method == 'TARGET_DIR':
            col.prop(tsynth_params, 'out_image_path')
            if MESSAGE:
                col.label(text=MESSAGE)
        if tsynth_params.out_method != 'OVERRIDE' or tsynth_params.gen_type == 'multi-generate':
            col.prop(tsynth_params, 'output_file_name')

        layout.operator("object.run_tsynthesis", icon='NODE_TEXTURE')
