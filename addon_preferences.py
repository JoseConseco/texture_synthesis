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
from pathlib import Path
from .tsynth_ui import TSYNTH_PT_TextureSynthesis
from .utils import get_addon_preferences


def check_file_exist(filePath):
    """Retuns absolute file path, and bool - file exist?"""
    abspathToFix = Path(bpy.path.abspath(filePath))  # crappy format like c:\\..\\...\\ddada.fbx
    outputPathStr = str(abspathToFix.resolve())
    if abspathToFix.is_dir():
        outputPathStr += '\\'
    return outputPathStr, os.path.isfile(outputPathStr)

panels = (
    TSYNTH_PT_TextureSynthesis,
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
    category: bpy.props.StringProperty(name="Tab Category", description="Choose a name for the category of the panel", default="Texture Synthesis", update=update_panel)
    display_info: bpy.props.StringProperty(name="Info", description="", default="")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "category", text="")
        col.prop(self, "text_synth_path", text="")
        col.label(text=self.display_info)
