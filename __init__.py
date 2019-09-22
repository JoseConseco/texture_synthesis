
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
#You need to download https://github.com/EmbarkStudios/texture-synthesis to use this addon.

#TODO:  why check_file_was_generated sometimes fails to load result?
#TODO:  multi input generate..
#TODO:  wait for inpaitn fix: https://github.com/EmbarkStudios/texture-synthesis/issues/41

bl_info = {
    "name": "Texture Synthesis",
    "author": "Jose Conseco",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Side Panel (N) > Tools",
    "description": "Textyre Synthesis",
    "warning": "",
    "wiki_url": "https://github.com/EmbarkStudios/texture-synthesis",
    "category": "Textures",
}

if "bpy" in locals():
    import importlib
    importlib.reload(get_image_size)
    importlib.reload(tsynth_props)
    importlib.reload(utils)
    importlib.reload(addon_preferences)
    importlib.reload(tsynth_ui)
    importlib.reload(main_operators)
else:
    from . import get_image_size
    from . import tsynth_props
    from . import utils
    from . import addon_preferences
    from . import tsynth_ui
    from . import main_operators

import bpy


# We can store multiple preview collections here,
# however in this example we only store "main"


classes = (
    addon_preferences.TextureSynthPreferences,
    tsynth_ui.TSYNTH_PT_TextureSynthesis,
    tsynth_ui.TSYNTH_PT_Previews,
    tsynth_props.TextSynth_Settings,
    main_operators.OBJECT_OT_TextureSynthesis,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tsynth_params = bpy.props.PointerProperty(type=tsynth_props.TextSynth_Settings)
    tsynth_props.register_thumbs()
    


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.context.scene.tsynth_params.my_previews
    del bpy.types.Scene.tsynth_params

    tsynth_props.unregister_thumbs()



