bl_info = {
    "name": "Proxy Generator",
    "author": "Sintesi Labs Design GmbH",
    "version": (0, 0, 2),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > Proxy Generator",
    "description": "Adds a UI panel to programmatically preview and generate proxy geometry for faster animation.",
    "wiki_url": "https://github.com/sintesilabs/blender-proxy-generator",
    "category": "3D View"
}


import bpy


# CONSTANTS

PROXY_DECIMATE_PREVIEW_NAME = "Proxy Decimate Preview"
PROXY_COLLECTION_NAME = "PROXIES"


# FUNCTIONS

def clear_proxy_preview(context):
    for object in context.selected_objects:
            if object.type == "MESH":
                bpy.context.view_layer.objects.active = object
                bpy.ops.object.modifier_remove(modifier=PROXY_DECIMATE_PREVIEW_NAME)


# PROPERTIES

class ProxyDecimateRatioProperty(bpy.types.PropertyGroup):
    ratio : bpy.props.FloatProperty(
        name = "Proxy Decimate Ratio",
        description = "Proxy Decimate Ratio",
        default = 0.1,
        min = 0.0,
        max = 1.0,
        step = 0.1,
        precision = 2,
    )


# OPERATORS

class OBJECT_OT_generate_proxy(bpy.types.Operator):

    bl_idname = "object.generate_proxy"
    bl_label = "Generate Proxy"
    bl_description = "Generate a Proxy Object for each of the selected Mesh objects"

    def execute(self, context):

        self.report({"INFO"}, "Generating proxies...")

        proxy_collection_exists = False
        proxies_collection = None

        for collection in bpy.data.collections:
            if collection.name == PROXY_COLLECTION_NAME:
                proxy_collection_exists = True
                proxies_collection = bpy.data.collections[PROXY_COLLECTION_NAME]
                break

        # Create PROXIES collection
        if proxy_collection_exists == False:
            proxies_collection = bpy.data.collections.new(PROXY_COLLECTION_NAME)
            proxies_collection.hide_render = True
            context.scene.collection.children.link(proxies_collection)

        # Copy selection and generate proxy meshes
        for object in context.selected_objects:
            if object.type == "MESH":
                # Create a copy of the object
                object_copy = object.copy()
                object_copy.hide_render = True
                object_copy.name = object.name + "_proxy"

                # Move to PROXIES collection
                proxies_collection.objects.link(object_copy)

                # Set Decimate modifier
                decimate_mod = object_copy.modifiers.new(name='Proxy Decimate', type='DECIMATE')
                proxy_decimate_ratio_property = bpy.context.scene.proxy_decimate_ratio_property
                decimate_mod.ratio = proxy_decimate_ratio_property.ratio

                # Apply
                bpy.context.view_layer.objects.active = object_copy
                bpy.ops.object.modifier_apply(modifier=decimate_mod.name, single_user=True)

                # Clear Proxy Previews
                clear_proxy_preview(context)

        return {"FINISHED"}


class OBJECT_OT_preview_proxy(bpy.types.Operator):
    bl_idname = "object.preview_proxy"
    bl_label = "Preview Proxy"
    bl_description = "Preview of a Proxy Object for each of the selected Mesh objects"

    def execute(self, context):
        proxy_decimate_ratio_property = bpy.context.scene.proxy_decimate_ratio_property
        for object in context.selected_objects:
            if object.type == "MESH":
                if PROXY_DECIMATE_PREVIEW_NAME not in object.modifiers:
                    object.modifiers.new(name=PROXY_DECIMATE_PREVIEW_NAME, type='DECIMATE')

                object.modifiers[PROXY_DECIMATE_PREVIEW_NAME].ratio = proxy_decimate_ratio_property.ratio

        return {"FINISHED"}


class OBJECT_OT_clear_proxy_preview(bpy.types.Operator):
    bl_idname = "object.clear_proxy_preview"
    bl_label = "Clear Preview"
    bl_description = "Remove non-destructive Decimate modifiers from the selected Mesh Objects"

    def execute(self, context):
        clear_proxy_preview(context)

        return {"FINISHED"}


# PANELS

class PROXY_GENERATOR_PT_panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Proxy Generator"
    bl_idname = "PROXY_GENERATOR_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proxy Generator"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        selected_objects = context.selected_objects
        target_objects = []

        # Filter out non-mesh objects
        for object in selected_objects:
            if object.type == "MESH":
                target_objects.append(object)


        row = layout.row()

        if len(target_objects) != 0:

            if len(target_objects) > 1:
                row.label(text="Selected mesh objects: " + str(len(target_objects)), icon='OBJECT_DATAMODE')
            else:
                row.label(text="Selected mesh object: " + obj.name, icon='OBJECT_DATAMODE')


            row = layout.row()
            row.prop(context.scene.proxy_decimate_ratio_property, "ratio", slider=True)
            row = layout.row()
            row.operator("object.preview_proxy", icon="MOD_DECIM")
            row.operator("object.clear_proxy_preview", icon="TRASH")

            row = layout.row()
            row.operator("object.generate_proxy", icon="DUPLICATE")

        else:
            row.label(text="Select mesh objects", icon='OBJECT_DATAMODE')

# (UN)REGISTER

classes = [
    ProxyDecimateRatioProperty,
    PROXY_GENERATOR_PT_panel,
    OBJECT_OT_generate_proxy,
    OBJECT_OT_preview_proxy,
    OBJECT_OT_clear_proxy_preview
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.proxy_decimate_ratio_property = bpy.props.PointerProperty(type=ProxyDecimateRatioProperty)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
