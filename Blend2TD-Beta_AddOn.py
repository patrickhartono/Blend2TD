# ---------------------- Addon info-----------------------

bl_info = {
    "name": "Blend2TD-Beta",
    "author": "Patrick Hartono (Based on Factory Settings v1.4.2)",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Panel",
    "description": "Export to TouchDesigner with GPU-accelerated POP operators (Blender 5.0+, TD 2025+)",
    "warning": "Modified version - Based on Factory Settings TD Scripts v1.4.2. Requires Blender 5.0+ and TouchDesigner 2025.32050+",
    "doc_url": "",
    "tracker_url": "https://github.com/patrickhartono/Blend2TD",
    "category": "Import-Export",
}


# ---------------------- Import-----------------------

import bpy
import os
import math
import numpy as np
import bmesh
import mathutils
from math import radians
from collections import Counter
import re
from bpy_extras.io_utils import axis_conversion
from mathutils import Matrix




# ---------------------- Material to clipboard class-----------------------

class VIEW3D_OT_ScriptToClipboard(bpy.types.Operator):
    """Script to clipboard"""
    bl_idname = 'export.to_script'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Script to Clipboard'
    bl_label = "Script to Clipboard"
    
    def execute(self, context):
        if not bpy.context.selected_objects:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}

        if not bpy.context.selected_objects[0].active_material:
            self.report({'ERROR'}, "No material selected for the active object")
            return {'CANCELLED'}
        
        def urlify(s):

        # Remove all non-word characters (everything except numbers and letters)
            s = re.sub(r"[^\w\s]", '', s)

        # Replace all runs of whitespace with a single dash
            s = re.sub(r"\s+", '_', s)
            
            return s
        
        #check image texture nodes
        def checkTex(input_socket):
            if input_socket.is_linked:
                link = input_socket.links[0]
                if link.from_node.type == 'TEX_IMAGE':
                    return bpy.path.abspath(link.from_node.image.filepath)
                else:
                    # Check all input sockets of the linked node recursively
                    for input_socket in link.from_node.inputs:
                        tex_path = checkTex(input_socket)
                        if tex_path is not None:
                            return tex_path
            return None
        
        #check version Blender
        if bpy.app.version[0] >= 5:
            emission = 'Emission Color'
        else:
            emission = 'Emission'
        
        material_list = [
        ['Base Color', 'basecolor'],
        ['Metallic', 'metallic'],
        ['Roughness', 'roughness'],
        [emission, 'emit'],
        ['Normal', 'normal'],
        ['Alpha', 'alpha']
        ]  
        
        material = bpy.context.selected_objects[0].active_material.name             # get name active material
                                                                                    
        active_material = bpy.data.materials[material]                              # enter data module by material name

        principled_shader = None  # Initialize to None before checking

        # Check if the material uses nodes
        if active_material.use_nodes:
            for node in active_material.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled_shader = node  # Found the Principled BSDF shader
                    break  # Exit the loop once found

        if principled_shader is None:
            self.report({'ERROR'}, "Only works with Principled BSDF shader")
            return {'CANCELLED'}
        
        for index, mat in enumerate(material_list):
            input_socket = principled_shader.inputs[mat[0]]
            texture_path = checkTex(input_socket)
            if texture_path is not None:
                material_list[index].append(texture_path)
            else:
                # Check if the default_value is a single value or a sequence (like a color)
                default_value = input_socket.default_value
                if isinstance(default_value, float):
                    material_list[index].append(default_value)
                else:
                    # Assume default_value is a sequence (tuple, list) if not a float
                    # Convert the tuple to a list to ensure consistency in data structure
                    material_list[index].extend(list(default_value))

        print(material_list)
        
        emitstrength = principled_shader.inputs['Emission Strength'].default_value
                        
        mat_name = str(material)
        mat_name = urlify(mat_name)

# ---------------------- to Blend2TD format-----------------------

        result = "#BLENDMATTOTD"        
        result += "\npbrName = '" +str(mat_name) + "'"
        result += "\nmat_list = " +str(material_list)
        result += "\nemitstrength = " +str(emitstrength)
        result += """\nparent(2).create(pbrMAT, f'{pbrName}_PBR')

matOp = parent(2).op(f'{pbrName}_PBR')
matOp.nodeX = parent().nodeX + matOp.nodeWidth *4.5
matOp.nodeY = parent().nodeY

count = 0
        
for x in mat_list:    
    #check if is path string
    if isinstance(x[2], str):
        parent(2).create(moviefileinTOP, f'{x[1]}_{pbrName}')
        createdOp = parent(2).op(f'{x[1]}_{pbrName}')
        createdOp.par.file = x[2]
    
        parent(2).create(nullTOP, f'{x[1]}_{pbrName}_null')
        createdNull = parent(2).op(f'{x[1]}_{pbrName}_null')
    
        createdOp.outputConnectors[0].connect(createdNull)

        createdOp.nodeX = parent().nodeX + parent().nodeWidth * 1.5
        createdOp.nodeY = parent().nodeY + createdOp.nodeHeight*(1.5 * count)
    
        createdNull.nodeX = createdOp.nodeX + createdOp.nodeWidth * 1.5
        createdNull.nodeY = createdOp.nodeY
        
        setattr(matOp.par, f'{x[1]}map', createdNull.name)
        
        count += 1
    else:
        if len(x) > 3 and x[0] != 'Normal':
            color_list = ['r','g','b']
            for id, i in enumerate(color_list):
                if x[1] == 'basecolor':
                    setattr(matOp.par, f'{x[1]}{i}', x[2+id])
                else:
                    setattr(matOp.par, f'{x[1]}{i}', x[2+id] * emitstrength)
        else:
            if x[0] != 'Normal' and x[0] != 'Alpha':
                setattr(matOp.par, f'{x[1]}', x[2])
            elif x[0] == 'Alpha':
                setattr(matOp.par, f'{x[1]}front', x[2])
"""
        
        bpy.context.window_manager.clipboard = result
        
        self.report({'INFO'}, "Script copied to Clipboard")
        
        return {'FINISHED'}

# ---------------------- end Material to clipboard class-----------------------


# ---------------------- Camera translate to clipboard class-----------------------

class CAMERA_OT_CameraToClipboard(bpy.types.Operator):
    bl_idname = 'camera.to_script'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Camera to Script'
    bl_label = 'Camera to Script'
    
    def execute(self, context):
        
        def urlify(s):
            # Remove all non-word characters (everything except numbers and letters)
            s = re.sub(r"[^\w\s]", '', s)

            # Replace all runs of whitespace with a single dash
            s = re.sub(r"\s+", '_', s)

            return s
        
        current_scene = bpy.context.scene
        
        # Check if the active camera is set in the scene
        if current_scene.camera is None:
            self.report({'ERROR'}, "No active camera in the scene")
            return {'CANCELLED'}
        
        active_cam = bpy.data.scenes[current_scene.name].camera
        cam_data_name = active_cam.data.name
        
        orig_fps = bpy.data.scenes[current_scene.name].render.fps
        
        # Compute the FOV based on sensor fit mode
        aspect_ratio = current_scene.render.resolution_x / current_scene.render.resolution_y
        sensor_fit = bpy.data.cameras[cam_data_name].sensor_fit
        cam_foc = bpy.data.cameras[cam_data_name].lens
        cam_width = bpy.data.cameras[cam_data_name].sensor_width
        cam_height = bpy.data.cameras[cam_data_name].sensor_height

        # Initialize the FOVs to None
        h_fov_deg = None
        v_fov_deg = None

        # Determine FOVs based on Sensor Fit Mode
        if sensor_fit == 'AUTO':
            # Determine the sensor size based on a 1:1 aspect ratio
            sensor_size = cam_width

            if aspect_ratio > 1:  # Width is greater
                h_fov_deg = 2 * math.degrees(math.atan(sensor_size / (2 * cam_foc)))
            else:  # Height is greater
                v_fov_deg = 2 * math.degrees(math.atan(sensor_size / (2 * cam_foc)))

        elif sensor_fit == 'HORIZONTAL':
            h_fov_deg = 2 * math.degrees(math.atan(cam_width / (2 * cam_foc)))

        elif sensor_fit == 'VERTICAL':
            v_fov_deg = 2 * math.degrees(math.atan(cam_height / (2 * cam_foc)))
        
        cam_name = str(active_cam.name)
        cam_name = urlify(cam_name)
        
        new_list = []
        
        #print('sensorsize: ' + str(sensor_size))
        #print('camwidth: ' +str(cam_width))
        #print('camheight: ' + str(cam_height))
        #print(' camfoc: ' + str(cam_foc))
        
        
        for f in range(current_scene.frame_start, current_scene.frame_end + 1, current_scene.frame_step):

            # go to frame f
            current_scene.frame_set(f)
            
            # output the camera matrix on the current frame
            m = active_cam.matrix_world.to_4x4()
            
            conv = axis_conversion(from_forward='-Y', from_up='Z',to_forward='Z',to_up='Y').to_4x4()
            
            m = conv @ m            
                
            def get_quaternion_from_euler(roll, pitch, yaw):
  
  #Convert an Euler angle to a quaternion.
   
  #Input
    #:param roll: The roll (rotation around x-axis) angle in radians.
    #:param pitch: The pitch (rotation around y-axis) angle in radians.
    #:param yaw: The yaw (rotation around z-axis) angle in radians.
 
  #Output
            #return qx, qy, qz, qw: The orientation in quaternion [x,y,z,w] format
                
                tx = m[0][3]
                ty = m[1][3]
                tz = m[2][3]
                
                qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
                qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
                qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
                qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
 
                return [tx, ty, tz, qx, qy, qz, qw]
            
            new_list.append(get_quaternion_from_euler(m.to_euler('XYZ')[0], m.to_euler('XYZ')[1], m.to_euler('XYZ')[2]))
            

        
        
                
# ---------------------- to Blend2TD format-----------------------

        result = "#BLENDCAMTOTD"
        result += "\nname = '" +cam_name + "'"
        result += '\norig_fps = ' +str(orig_fps)
        result += '\ncam_hfov = ' +str(h_fov_deg)
        result += '\ncam_vfov = ' +str(v_fov_deg)
        result += '\nanim_list = ' +str(new_list)
        result += '\nlength_frames = ' +str(len(new_list))
        result += """\ncam_list = parent(2).findChildren(name=name)

if len(cam_list) == 0:
    parent(2).create(cameraCOMP, name)
else:
    pass

anim_table_name = name + '_data'
anim_table_list = parent(2).findChildren(name=anim_table_name)

if len(anim_table_list) == 0:
    parent(2).create(textDAT, anim_table_name)
    parent(2).create(dattoCHOP, name + '_datto')
    parent(2).create(stretchCHOP, name + '_stretch')
    parent(2).create(nullCHOP, name + '_null')
    parent(2).create(mergeCHOP, name + '_merge')
    parent(2).create(angleCHOP, name + '_angle')
    parent(2).create(selectCHOP, name + '_select1')
    parent(2).create(selectCHOP, name + '_select2')
else:
    pass

createdCamera = eval("parent(2).op('{}')".format(name))
createdTable = eval("parent(2).op('{}')".format(anim_table_name))
createdDatto = eval("parent(2).op('{}')".format(name + '_datto'))
createdStretch = eval("parent(2).op('{}')".format(name + '_stretch'))
createdNull = eval("parent(2).op('{}')".format(name + '_null'))
createdMerge = eval("parent(2).op('{}')".format(name + '_merge'))
createdAngle = eval("parent(2).op('{}')".format(name + '_angle'))
createdSelect1 = eval("parent(2).op('{}')".format(name + '_select1'))
createdSelect2 = eval("parent(2).op('{}')".format(name + '_select2'))

createdTable.nodeX = parent().nodeX + (parent().nodeWidth /2)
createdTable.nodeY = parent().nodeY 

createdDatto.nodeX = createdTable.nodeX
createdDatto.nodeY = createdTable.nodeY - createdTable.nodeHeight*3

createdStretch.nodeX = createdDatto.nodeX + me.nodeWidth * 1.5
createdStretch.nodeY = createdDatto.nodeY

createdSelect1.nodeX = createdStretch.nodeX
createdSelect1.nodeY = createdStretch.nodeY -me.nodeHeight * 1.5

createdSelect2.nodeX = createdStretch.nodeX + me.nodeWidth * 1.5
createdSelect2.nodeY = createdStretch.nodeY

createdAngle.nodeX = createdSelect2.nodeX
createdAngle.nodeY = createdSelect1.nodeY

createdMerge.nodeX = createdSelect2.nodeX + me.nodeWidth * 1.5
createdMerge.nodeY = createdStretch.nodeY

createdCamera.nodeX = createdStretch.nodeX
createdCamera.nodeY = createdTable.nodeY

createdNull.nodeX = createdCamera.nodeX 
createdNull.nodeY = createdCamera.nodeY - me.nodeHeight*1.5

createdDatto.outputConnectors[0].connect(createdStretch)
createdSelect2.outputConnectors[0].connect(createdMerge.inputConnectors[0])
createdAngle.outputConnectors[0].connect(createdMerge.inputConnectors[1])
createdMerge.outputConnectors[0].connect(createdNull)
createdSelect1.outputConnectors[0].connect(createdAngle)


createdDatto.par.dat = anim_table_name
createdDatto.par.output = 2
createdDatto.par.firstrow = 1
createdDatto.par.firstcolumn = 2

createdStretch.par.scale.expr = 'me.time.rate / ' + str(orig_fps)

createdSelect1.par.chop = createdStretch.name
createdSelect1.par.channames = 'x y z w'

createdAngle.par.inunit = 2

createdSelect2.par.chop = createdStretch.name
createdSelect2.par.channames = 'tx ty tz'

if cam_hfov == None:
    createdCamera.par.viewanglemethod = 1
    createdCamera.par.fov = cam_vfov
else:
    createdCamera.par.viewanglemethod = 0
    createdCamera.par.fov = cam_hfov

createdCamera.par.tx.expr = "op('{}')[0]".format(createdNull.name)
createdCamera.par.ty.expr = "op('{}')[1]".format(createdNull.name)
createdCamera.par.tz.expr = "op('{}')[2]".format(createdNull.name)
createdCamera.par.rx.expr = "op('{}')[3]".format(createdNull.name)
createdCamera.par.ry.expr = "op('{}')[4]".format(createdNull.name)
createdCamera.par.rz.expr = "op('{}')[5]".format(createdNull.name)

createdDatto.dock = createdTable
createdDatto.showDocked = 0

createdStretch.dock = createdTable
createdStretch.showDocked = 0

createdSelect1.dock = createdTable
createdSelect1.showDocked = 0

createdSelect2.dock = createdTable
createdSelect2.showDocked = 0

createdAngle.dock = createdTable
createdAngle.showDocked = 0

createdMerge.dock = createdTable
createdMerge.showDocked = 0

createdTable.dock = createdCamera
createdTable.showDocked = 0

createdNull.dock = createdCamera
createdNull.showDocked = 0

createdTable.clear()
createdTable.appendRow(['tx','ty','tz','x','y','z','w'])

check_list = []

for x in anim_list:
    createdTable.appendRow(x)
    check_list.append(sum(x))

sum_check_list = sum(check_list)
result = sum_check_list / check_list[0]
result = round(result,5)

if length_frames > 1:
    if result == length_frames:
        delete = list(range(2,int(float(length_frames))+1))
        createdTable.deleteRows(delete)
    else:
        pass"""
        
        bpy.context.window_manager.clipboard = result        
   
        self.report({'INFO'}, "Script copied to Clipboard")
        
        return {'FINISHED'}
    
# ---------------------- end Camera translate to clipboard class-----------------------


# ---------------------- Mesh to clipboard class-----------------------

class MESH_OT_MeshToClipboard(bpy.types.Operator):
    bl_idname = 'mesh.to_script'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Mesh to Script'
    bl_label = 'Mesh to Script'
    
    def execute(self, context):
        if not bpy.context.selected_objects:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}

        def urlify(s):

    # Remove all non-word characters (everything except numbers and letters)
            s = re.sub(r"[^\w\s]", '', s)

    # Replace all runs of whitespace with a single dash
            s = re.sub(r"\s+", '_', s)

            return s
        
        # Check if there's a selected object
        obj = bpy.context.active_object
        if obj is None:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}
        
        dg = bpy.context.evaluated_depsgraph_get()
        
        obj = obj.evaluated_get(dg) #collapse modifiers
        
        obj_data = obj.data
        
        bm = bmesh.new()
        bm.from_mesh(obj_data)
        
        bm.transform(obj.matrix_world)
        
        matrix = axis_conversion(from_forward='-Y', from_up='Z',to_forward='Z',to_up='Y').to_4x4()
        # Use the matrix to transform all vertices
        
        for vert in bm.verts:
            vert.co = matrix @ vert.co
            vert.normal = matrix.to_3x3() @ vert.normal
        
        verts_coords = np.empty((len(bm.verts), 7))
                
        for i, vert in enumerate(bm.verts):
            verts_coords[i][0] = int(i)
            verts_coords[i][1] = vert.co[0]
            verts_coords[i][2] = vert.co[1]
            verts_coords[i][3] = vert.co[2]
            verts_coords[i][4] = vert.normal[0]
            verts_coords[i][5] = vert.normal[1]
            verts_coords[i][6] = vert.normal[2]         

        bpy.ops.object.mode_set(mode='OBJECT')

        obj_name = str(obj.name)
        obj_name = urlify(obj_name)
        
        primsDatList = []
        vertsDatList = []
        
        uv_layer = bm.loops.layers.uv.active if bm.loops.layers.uv else None  # Check for active UV layer
        
        for i, face in enumerate(bm.faces):
            vertices_str = ' '.join(str(vertex.index) for vertex in face.verts)
            primsDatList.append([face.index, vertices_str, 1])
            
            for j, loop in enumerate(face.loops):
                if uv_layer:  # If there's an active UV layer
                    uv_coords = loop[uv_layer].uv
                    vertsDatList.append([i, j, uv_coords.x, uv_coords.y])
                else:
                    vertsDatList.append([i, j])


        verts_coords = verts_coords.tolist()
        
                
# ---------------------- to Blend2TD format-----------------------

        result = "#BLENDMESHTOTD"
        result += '\nfrom collections import Counter'
        result += '\nimport itertools'
        result += '\nimport numpy as np'
        result += '\npointsDatList = np.array(' + str(verts_coords) + ')'
        result += '\nprimsDatList = ' + str(primsDatList)
        result += '\nvertsDatList = np.array(' + str(vertsDatList) + ')'
        result += '\nobject_name = ' + "'" +obj_name + "'"
        result +="""\nfind_datto = parent(2).findChildren(name=object_name)

if len(find_datto) == 0:

    parent(2).create(dattoSOP, object_name )
    createdOp = eval("parent(2).op('{}')".format(object_name ))

    createdOp.nodeX = parent().nodeX + parent().nodeWidth * 1.5
    createdOp.nodeY = parent().nodeY

    parent(2).create(tableDAT, str(object_name) + '_points' )
    pointsDat = eval("parent(2).op('{}')".format(str(object_name) + '_points' ))
    pointsDat.nodeX = createdOp.nodeX
    pointsDat.nodeY = createdOp.nodeY - pointsDat.nodeHeight * 1.5

    pointsDat.dock = createdOp
    pointsDat.showDocked = 0

    parent(2).create(tableDAT, str(object_name) + '_polygons' )
    primsDat = eval("parent(2).op('{}')".format(str(object_name) + '_polygons' ))
    primsDat.nodeX = createdOp.nodeX + primsDat.nodeWidth * 1.5
    primsDat.nodeY = createdOp.nodeY - primsDat.nodeHeight * 1.5

    primsDat.dock = createdOp
    primsDat.showDocked = 0

    parent(2).create(tableDAT, str(object_name) + '_vertices' )
    verticesDat = eval("parent(2).op('{}')".format(str(object_name) + '_vertices' ))
    verticesDat.nodeX = createdOp.nodeX + verticesDat.nodeWidth * 3
    verticesDat.nodeY = createdOp.nodeY - verticesDat.nodeHeight * 1.5

    verticesDat.dock = createdOp
    verticesDat.showDocked = 0
    
else:
    createdOp = eval("parent(2).op('{}')".format(object_name ))
    pointsDat = eval("parent(2).op('{}')".format(str(object_name) + '_points' ))
    primsDat = eval("parent(2).op('{}')".format(str(object_name) + '_polygons' ))
    verticesDat = eval("parent(2).op('{}')".format(str(object_name) + '_vertices' ))
    
    
pointsDat.clear()
primsDat.clear()
verticesDat.clear()

for x in pointsDatList:
    pointsDat.appendRow(x)
pointsDat.insertRow(['index', 'P(0)','P(1)','P(2)','N(0)','N(1)','N(2)'])

for x in primsDatList:
    primsDat.appendRow(x)
primsDat.insertRow(['index', 'vertices', 'close'])

for x in vertsDatList:
    verticesDat.appendRow(x)
verticesDat.insertRow(['index','vindex','uv(0)','uv(1)'])
    
createdOp.par.pointsdat = str(pointsDat.name)
createdOp.par.verticesdat = str(verticesDat.name)
createdOp.par.primsdat = str(primsDat.name)

# Auto-generate SOP to POP conversion for GPU acceleration
soptopop_name = object_name + '_POP'
parent(2).create(soptoPOP, soptopop_name)
createdPOP = parent(2).op(soptopop_name)

createdPOP.nodeX = createdOp.nodeX + createdOp.nodeWidth * 1.5
createdPOP.nodeY = createdOp.nodeY

# Connect dattoSOP to soptoPOP
createdPOP.par.sop = createdOp.path
"""
        
        bpy.context.window_manager.clipboard = result        
   
        self.report({'INFO'}, "Script copied to Clipboard")
        
        bm.free()
        
        return {'FINISHED'}
    
# ---------------------- end Mesh to clipboard class-----------------------


# ---------------------- Export UV-Map to clipboard class-----------------------

class UV_OT_UVMapToClipboard(bpy.types.Operator):
    bl_idname = 'uvmap.to_script'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UVMap to Script'
    bl_label = 'UVMap to Script'
    
    def execute(self, context):
        
        def urlify(s):

    # Remove all non-word characters (everything except numbers and letters)
            s = re.sub(r"[^\w\s]", '', s)

    # Replace all runs of whitespace with a single dash
            s = re.sub(r"\s+", '_', s)

            return s
        
        # Check if there's a selected object
        obj = bpy.context.active_object
        if obj is None:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}

        # Check if the selected object has an active UV map
        if obj.data.uv_layers.active is None:
            self.report({'ERROR'}, "No active UV Map")
            return {'CANCELLED'}
        
        obj = bpy.context.active_object
        
        num_faces = len(obj.data.polygons)
        
        uvCoord_x = [(data.uv.x) for data in obj.data.uv_layers.active.data]
        uvCoord_y = [(data.uv.y) for data in obj.data.uv_layers.active.data]
        
        face_list = []
        
        obj_data = obj.data
        bm = bmesh.new()
        bm.from_mesh(obj_data)
        
        for x in bm.faces:
            for v in x.verts:
                face_list.append(x.index)
        
        obj_name = str(obj.name)
        obj_name = urlify(obj_name)
        
                
# ---------------------- to Blend2TD format-----------------------

        result = "#BLENDUVTOTD"
        result += '\nface_list = ' + str(face_list)
        result += '\nuvCoord_x_list = ' + str(uvCoord_x)
        result += '\nuvCoord_y_list = ' + str(uvCoord_y)
        result += '\nnum_faces = ' + str(num_faces)
        result += '\nuv_name = ' + "'" +obj_name + '_UVMap' + "'"
        result += """\nfind_datto = parent(2).findChildren(name=uv_name)

if len(find_datto) == 0:

    parent(2).create(dattoSOP, uv_name )
    createdOp = eval("parent(2).op('{}')".format(uv_name ))

    createdOp.nodeX = parent().nodeX + parent().nodeWidth * 1.5
    createdOp.nodeY = parent().nodeY

    parent(2).create(tableDAT, str(uv_name) + '_points' )
    pointsDat = eval("parent(2).op('{}')".format(str(uv_name) + '_points' ))
    pointsDat.nodeX = createdOp.nodeX
    pointsDat.nodeY = createdOp.nodeY - pointsDat.nodeHeight * 1.5

    pointsDat.dock = createdOp
    pointsDat.showDocked = 0

    parent(2).create(tableDAT, str(uv_name) + '_polygons' )
    primsDat = eval("parent(2).op('{}')".format(str(uv_name) + '_polygons' ))
    primsDat.nodeX = createdOp.nodeX + primsDat.nodeWidth * 1.5
    primsDat.nodeY = createdOp.nodeY - primsDat.nodeHeight * 1.5

    primsDat.dock = createdOp
    primsDat.showDocked = 0

    parent(2).create(tableDAT, str(uv_name) + '_vertices' )
    verticesDat = eval("parent(2).op('{}')".format(str(uv_name) + '_vertices' ))
    verticesDat.nodeX = createdOp.nodeX + verticesDat.nodeWidth * 3
    verticesDat.nodeY = createdOp.nodeY - verticesDat.nodeHeight * 1.5

    verticesDat.dock = createdOp
    verticesDat.showDocked = 0
    
    parent(2).create(baseCOMP, uv_name + '_base')
    base = eval("parent(2).op('{}')".format(uv_name + '_base' ))
    base.nodeX = createdOp.nodeX + createdOp.nodeWidth * 1.5
    base.nodeY = createdOp.nodeY
    
    base.create(inSOP, uv_name + '_null')
    createdNull = eval("parent(2).op('{}')".format(base.name + '/' + uv_name + '_null' ))
    
    base.inputConnectors[0].connect(createdOp)
    
    base.create(geometryCOMP, uv_name + '_geo')
    createdGeo = eval("parent(2).op('{}')".format(base.name + '/' + uv_name + '_geo' ))
    createdGeo.nodeX = createdNull.nodeX + createdNull.nodeWidth * 1.5
    createdGeo.nodeY = createdNull.nodeY
    del_torus = createdGeo.findChildren(name='torus1')
    del_torus[0].destroy()
    
    createdGeo.create(inSOP, 'in1')
    createdGeo.op('in1').display = 1
    createdGeo.op('in1').render = 1
    
    createdGeo.inputConnectors[0].connect(createdNull)
    
    base.create(renderTOP, uv_name + '_render')
    createdRender = eval("parent(2).op('{}')".format(base.name + '/' + uv_name + '_render' ))
    createdRender.nodeX = createdGeo.nodeX + createdGeo.nodeWidth * 1.5
    createdRender.nodeY = createdGeo.nodeY
    
    createdRender.par.geometry.val = createdGeo.name
    
    base.create(cameraCOMP, uv_name + '_cam')
    createdCam = eval("parent(2).op('{}')".format(base.name + '/' + uv_name + '_cam' ))
    createdCam.nodeX = createdGeo.nodeX 
    createdCam.nodeY = createdGeo.nodeY - createdGeo.nodeHeight * 1.5
    
    base.create(lineMAT, uv_name + '_mat')
    createdMat = eval("parent(2).op('{}')".format(base.name + '/' + uv_name + '_mat' ))
    createdMat.nodeX = createdGeo.nodeX 
    createdMat.nodeY = createdGeo.nodeY + createdGeo.nodeHeight * 1.5
    
    base.create(transformTOP, uv_name + '_trans')
    createdTrans = eval("parent(2).op('{}')".format(base.name + '/' + uv_name + '_trans' ))
    createdTrans.nodeX = createdRender.nodeX + createdRender.nodeWidth * 1.5
    createdTrans.nodeY = createdRender.nodeY 
    
    createdRender.outputConnectors[0].connect(createdTrans)
    
    base.create(outTOP, uv_name + '_out')
    createdOut = eval("parent(2).op('{}')".format(base.name + '/' + uv_name + '_out' ))
    createdOut.nodeX = createdTrans.nodeX + createdTrans.nodeWidth * 1.5
    createdOut.nodeY = createdTrans.nodeY
    
    createdTrans.outputConnectors[0].connect(createdOut)
    
    createdGeo.par.material = createdMat.name
    createdRender.par.camera = createdCam.name
    createdCam.par.projection = 1
    createdCam.par.orthowidth = 1
    createdCam.par.winx = .5
    createdCam.par.winy = .5
    
    createdRender.par.resolutionw = 1080
    createdRender.par.resolutionh = 1080
    
    createdTrans.par.bgcolora = 1
    createdTrans.par.compover = 1
    
    base.par.opviewer = './' + createdOut.name
    base.viewer = 1
    
        
else:
    createdOp = eval("parent(2).op('{}')".format(uv_name ))
    pointsDat = eval("parent(2).op('{}')".format(str(uv_name) + '_points' ))
    primsDat = eval("parent(2).op('{}')".format(str(uv_name) + '_polygons' ))
    verticesDat = eval("parent(2).op('{}')".format(str(uv_name) + '_vertices' ))
    
pointsDat.clear()
primsDat.clear()
verticesDat.clear()

from_list = [0]     
to_list = []

# While iterating through indices and values, use enumerate
for i,x in enumerate(face_list):       # iterate through all indices
    if i == 0 or i == (len(face_list)-1):  # pass the first and last index
        pass
    else:
        pre = face_list[i-1]                
        post = face_list [i+1]            
        
        if post > x:
            from_list.append(i+1)
            to_list.append(i+1)

to_list.append(len(face_list))

verts_list = []

for x in range(len(face_list)):
    verts_list.append(x)

verts_list = [str(x) for x in verts_list]

for x,y in zip(from_list,to_list): 
    
    primsDat.appendRow( [' '.join(verts_list[x:y])] )

closed = ['1' for i in range(num_faces)]

primsDat.insertCol(range(0,num_faces))
primsDat.appendCol(closed)
primsDat.insertRow(['index', 'vertices', 'close'])

pointsDat.appendCol(range(0,len(uvCoord_x_list)))
pointsDat.appendCol(uvCoord_x_list)
pointsDat.appendCol(uvCoord_y_list)
pointsDat.insertRow(['index', 'P(0)','P(1)'])

createdOp.par.pointsdat = str(pointsDat.name)
createdOp.par.primsdat = str(primsDat.name)
    
"""


        
        bpy.context.window_manager.clipboard = result        
   
        self.report({'INFO'}, "Script copied to Clipboard")
        
        bm.free()
        
        return {'FINISHED'}
    
# ---------------------- end Export UV-Map to clipboard class-----------------------




# ---------------------- BETA FEATURES ------------------------------------

# ---------------------- start Multimat class-----------------------

class BETA_OT_MultiMatPOP(bpy.types.Operator):
    bl_idname = 'beta_multi_mat_pop.to_script'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MultiMat to Script'
    bl_label = 'MultiMat POP to Script'
    
    
    def execute(self, context):
            if not bpy.context.selected_objects:
                self.report({'ERROR'}, "No object selected")
                return {'CANCELLED'}

            def urlify(s):

        # Remove all non-word characters (everything except numbers and letters)
                s = re.sub(r"[^\w\s]", '', s)

        # Replace all runs of whitespace with a single dash
                s = re.sub(r"\s+", '_', s)

                return s
            
            # Check if there's a selected object
            obj = bpy.context.active_object
            if obj is None:
                self.report({'ERROR'}, "No object selected")
                return {'CANCELLED'}
            
            # Get the active object
            obj = bpy.context.active_object

            # Check if the selected object has any materials
            if not obj.material_slots:
                self.report({'ERROR'}, "No material assigned to the selected object")
                return {'CANCELLED'}
            
            # Check if any material has a Principled BSDF node
            principled_found = False
            for mat_slot in obj.material_slots:
                if mat_slot.material and mat_slot.material.use_nodes:
                    for node in mat_slot.material.node_tree.nodes:
                        if node.type == 'BSDF_PRINCIPLED':
                            principled_found = True
                            break
            
            if not principled_found:
                self.report({'ERROR'}, "Add material with a Principled BSDF node")
                return {'CANCELLED'}
            
            def checkTex(input_socket):
                """Recursively search for an image texture node starting from the input_socket."""
                if input_socket.is_linked:
                    link = input_socket.links[0]
                    if link.from_node.type == 'TEX_IMAGE':
                        return bpy.path.abspath(link.from_node.image.filepath)
                    else:
                        # Check all input sockets of the linked node recursively
                        for input_socket in link.from_node.inputs:
                            tex_path = checkTex(input_socket)
                            if tex_path is not None:
                                return tex_path
                return None
            
            material_data_list = []

            #check version Blender
            if bpy.app.version[0] >= 5:
                emission = 'Emission Color'
            else:
                emission = 'Emission'

            for slot in obj.material_slots:
                if slot.material:
                    mat = slot.material
                    if mat.use_nodes:
                        for node in mat.node_tree.nodes:
                            if node.type == 'BSDF_PRINCIPLED':
                                material_data = {}            
                                material_data["name"] = urlify(mat.name)
                                material_data["basecolor_tex"] = checkTex(node.inputs['Base Color'])
                                material_data["metallic_tex"] = checkTex(node.inputs['Metallic'])
                                material_data["roughness_tex"] = checkTex(node.inputs['Roughness'])
                                material_data["normal_tex"] = checkTex(node.inputs['Normal'])
                                material_data["emitcolor_tex"] = checkTex(node.inputs[emission])                            
                                material_data["basecolor_r"] = node.inputs['Base Color'].default_value[0]
                                material_data["basecolor_g"] = node.inputs['Base Color'].default_value[1]
                                material_data["basecolor_b"] = node.inputs['Base Color'].default_value[2]
                                material_data["basecolor_a"] = node.inputs['Base Color'].default_value[3]
                                material_data["metallic"] = node.inputs['Metallic'].default_value
                                material_data["roughness"] = node.inputs['Roughness'].default_value
                                material_data["emitcolor_r"] = node.inputs[emission].default_value[0]
                                material_data["emitcolor_g"] = node.inputs[emission].default_value[1]
                                material_data["emitcolor_b"] = node.inputs[emission].default_value[2]
                                material_data["emitcolor_a"] = node.inputs[emission].default_value[3]
                                material_data["emitstrength"] = node.inputs['Emission Strength'].default_value
                                
                                material_data_list.append(material_data)

                    
            dg = bpy.context.evaluated_depsgraph_get()
            
            obj = obj.evaluated_get(dg) #collapse modifiers
            
            obj_data = obj.data
            
            bm = bmesh.new()
            bm.from_mesh(obj_data)
            
            bm.transform(obj.matrix_world)
            
            matrix = axis_conversion(from_forward='-Y', from_up='Z',to_forward='Z',to_up='Y').to_4x4()
            # Use the matrix to transform all vertices
            
            face_vertex_material_ids = []
            num_mats = len(obj.material_slots)

            for face in bm.faces:
                mat_id = face.material_index
                for vertex in face.verts:
                    face_vertex_material_ids.append(mat_id)                 
            
            for vert in bm.verts:
                vert.co = matrix @ vert.co
                vert.normal = matrix.to_3x3() @ vert.normal
            
            verts_coords = np.empty((len(bm.verts), 7), dtype=np.float32)
            
                    
            for i, vert in enumerate(bm.verts):
                verts_coords[i][0] = int(i)
                verts_coords[i][1] = vert.co[0]
                verts_coords[i][2] = vert.co[1]
                verts_coords[i][3] = vert.co[2]
                verts_coords[i][4] = vert.normal[0]
                verts_coords[i][5] = vert.normal[1]
                verts_coords[i][6] = vert.normal[2]         

            bpy.ops.object.mode_set(mode='OBJECT')

            obj_name = str(obj.name)
            obj_name = urlify(obj_name)
            
            primsDatList = []

            # Get the number of UV channels (which is number of UV layers multiplied by 3)
            uv_channel_count = len(bm.loops.layers.uv) * 3
            
            # Get number of UV layers.
            num_uv_layers = len(bpy.context.object.data.uv_layers)

            # Get active vertex color layer if exists.
            vertex_color_layer = 1 if len(obj_data.vertex_colors) > 0 else 0

            # Check the number of materials.
            num_materials = len(obj_data.materials)

            # Calculate the length of the array for each vertex.
            length = 2 + 3*num_uv_layers + (4 if vertex_color_layer else 0) + (1 if num_materials else 0)

            # Create an empty numpy array with shape (number of loop vertices, calculated length)
            vertsDatList = np.zeros((len(obj_data.loops), length), dtype=np.float32)
            
            
            
            # If the active vertex color layer exists, fetch its name
            if obj_data.vertex_colors:
                active_vc_name = obj_data.vertex_colors.active.name
                vc_layer = bm.loops.layers.color.get(active_vc_name)
            else:
                vc_layer = None
            
            loopCount = 0
            
            for i, face in enumerate(bm.faces):
                vertices_str = ' '.join(str(vertex.index) for vertex in face.verts)
                primsDatList.append([face.index, vertices_str, 1])
                
                
                
                for j, loop in enumerate(face.loops):
                    uv_coords_list = []
                    for uv_layer in bm.loops.layers.uv.values():
                        uv_coords = loop[uv_layer].uv
                        uv_coords_list.extend([uv_coords.x, uv_coords.y, 0.0])  # Appending the UVs and the 0.0 for 'w'

                    # Fetch vertex color data if the layer exists
                    if vertex_color_layer == 1:
                        col = loop[vc_layer]
                        color_data = [col[0], col[1], col[2], col[3]]  # RGBA
                    else:
                        color_data = []
                    
                    loopCount += 1
                    
                    verts_entry = [int(i), int(j)] + uv_coords_list + color_data
                    
                    for idx, value in enumerate(verts_entry):
                        vertsDatList[loopCount -1][idx] = value
                        
                        
            for idx, mat_id in enumerate(face_vertex_material_ids):
                vertsDatList[idx][-1] = mat_id    
            
            verts_coords = verts_coords.tolist()
            vertsDatList = vertsDatList.tolist()
            
            
            
            
                    
    # ---------------------- to Blend2TD format-----------------------

            result = "#BLENDMESHTOTD"
            result += '\nfrom collections import Counter'
            result += '\nimport itertools'
            result += '\nimport numpy as np'
            result += '\npointsDatList = np.array(' + str(verts_coords) + ')'
            result += '\nprimsDatList = ' + str(primsDatList)
            result += '\nvertsDatList = np.array(' + str(vertsDatList) + ')'
            result += '\nobject_name = ' + "'" +obj_name + "'"
            result += '\nmaterial_list = ' + str(material_data_list)
            result += '\nnum_mats = ' + str(num_mats)
            result += '\nnum_uvs = ' + str(uv_channel_count)
            result += '\nvert_col_num = ' + str(vertex_color_layer)
            result +="""\nfind_datto = parent(2).findChildren(name=object_name)

if len(find_datto) == 0:

    parent(2).create(dattoPOP, object_name)
    createdOp = parent(2).op(f'{object_name}')

    createdOp.nodeX = parent().nodeX + parent().nodeWidth * 1.5
    createdOp.nodeY = parent().nodeY

    parent(2).create(nullPOP, f'{object_name}_null')
    createdNull = parent(2).op(f'{object_name}_null')

    createdNull.nodeX = parent().nodeX + parent().nodeWidth * 2.5
    createdNull.nodeY = parent().nodeY

    parent(2).create(geometryCOMP, f'{object_name}_GEO')
    createdGEO = parent(2).op(f'{object_name}_GEO')

    createdGEO.nodeX = parent().nodeX + parent().nodeWidth * 3.5
    createdGEO.nodeY = parent().nodeY

    createdOp.outputConnectors[0].connect(createdNull)

    createdGEO.create(inPOP, f'{object_name}_in')
    createdIn = parent(2).op(f'{createdGEO.name}/{object_name}_in')
    createdGEO.op('torus1').destroy()

    createdGEO.create(attributecreatePOP, f'{object_name}_tangents')
    createdTangents = parent(2).op(f'{createdGEO.name}/{object_name}_tangents')
    createdTangents.nodeX = createdIn.nodeX + createdIn.nodeWidth * 1.25    

    createdGEO.inputConnectors[0].connect(createdNull)
    createdIn.outputConnectors[0].connect(createdTangents)

    createdTangents.render = 1
    createdTangents.display = 1
    createdTangents.par.comptang = 1

    # if num_mats == 0

    createdGEO.create(glslMAT, f'{object_name}_glsl')
    createdGLSL = parent(2).op(f'{createdGEO.name}/{object_name}_glsl')
    createdGLSL.nodeX = createdTangents.nodeX + createdTangents.nodeWidth * 1.25

    createdVertex = parent(2).op(f'{createdGEO.name}/{createdGLSL.name}_vertex')
    createdVertex.showDocked = 0
    createdPixel = parent(2).op(f'{createdGEO.name}/{createdGLSL.name}_pixel')
    createdPixel.showDocked = 0
    
    createdGEO.op(f'{object_name}_glsl_info').showDocked = 0

    parent(2).create(tableDAT, f'{object_name}_points')
    pointsDat = parent(2).op(f'{object_name}_points')
    pointsDat.nodeX = createdOp.nodeX
    pointsDat.nodeY = createdOp.nodeY - pointsDat.nodeHeight * 1.5

    pointsDat.dock = createdOp
    pointsDat.showDocked = 0

    parent(2).create(tableDAT, f'{object_name}_polygons')
    primsDat = parent(2).op(f'{object_name}_polygons')
    primsDat.nodeX = createdOp.nodeX + primsDat.nodeWidth * 1.5
    primsDat.nodeY = createdOp.nodeY - primsDat.nodeHeight * 1.5

    primsDat.dock = createdOp
    primsDat.showDocked = 0

    parent(2).create(tableDAT, f'{object_name}_vertices')
    verticesDat = parent(2).op(f'{object_name}_vertices')
    verticesDat.nodeX = createdOp.nodeX + verticesDat.nodeWidth * 3
    verticesDat.nodeY = createdOp.nodeY - verticesDat.nodeHeight * 1.5

    verticesDat.dock = createdOp
    verticesDat.showDocked = 0
    
else:
    createdOp = parent(2).op(f'{object_name}')
    createdNull = parent(2).op(f'{object_name}_null')
    createdGEO = parent(2).op(f'{object_name}_GEO')
    createdIn = parent(2).op(f'{createdGEO.name}/{object_name}_in')
    createdTangents = parent(2).op(f'{createdGEO.name}/{object_name}_tangents')
    pointsDat = parent(2).op(f'{object_name}_points')
    primsDat = parent(2).op(f'{object_name}_polygons')
    verticesDat = parent(2).op(f'{object_name}_vertices')
    createdGLSL = parent(2).op(f'{createdGEO.name}/{object_name}_glsl')
    createdVertex = parent(2).op(f'{createdGEO.name}/{createdGLSL.name}_vertex')
    createdPixel = parent(2).op(f'{createdGEO.name}/{createdGLSL.name}_pixel')
    
    
    
pointsDat.clear()
primsDat.clear()
verticesDat.clear()
createdGEO.destroyCustomPars()

createdVertex.clear()
createdPixel.clear()

parent().store('mat_list', material_list)
parent().store('animated', 'False')

for x in pointsDatList:
    pointsDat.appendRow(x)
pointsDat.insertRow(['index', 'P(0)','P(1)','P(2)','N(0)','N(1)','N(2)'])

for x in primsDatList:
    primsDat.appendRow(x)
primsDat.insertRow(['index', 'vertices', 'close'])

for x in vertsDatList:
    verticesDat.appendRow(x)

verticesDatNameList = []

verticesDatNameList.append('index')
verticesDatNameList.append('vindex')

if num_uvs > 0:
    for x in range(num_uvs):
        verticesDatNameList.append('Tex(' +str(int(x)) + ')')
else:
    pass

if vert_col_num > 0:
    for x in range(4):
        verticesDatNameList.append('Color(' + str(int(x)) + ')')

if num_mats > 0:
    verticesDatNameList.append('attrib')
else:
    pass
    
verticesDat.insertRow(verticesDatNameList)
    
createdOp.par.pointsdat = str(pointsDat.name)
createdOp.par.verticesdat = str(verticesDat.name)
createdOp.par.primsdat = str(primsDat.name)
createdOp.par.int = '*'


# write to shader
createdVertex.write(op('vertexShader').text)
parent().WriteToFragment(createdPixel)

createdGEO.par.material = './' + str(createdGLSL.name)

names = [material['name'] for material in material_list]

createdGLSL.par.sampler0.sequence.numBlocks = 1

for id, material in enumerate(names):
    parent().CreateParPage(str(object_name), material, id, id+id)
    
op('offset').par.value0 = 0
op('offset').par.value1 = 0

existingMaterials = createdGEO.findChildren(type=baseCOMP)
compareList = []

for x in existingMaterials:
    compareList.append(x.name)    

destroyList = set(names) ^ set(compareList)

for x in destroyList:
    createdGEO.op(f'{x}').destroy()
    
parent().unstore('*')

"""
            
            bpy.context.window_manager.clipboard = result        
       
            self.report({'INFO'}, "Script copied to Clipboard")
            
            bm.free()
            
            return {'FINISHED'}
    
    
# ---------------------- End Placeholder Multimat class-----------------------

# ---------------------- Anim Mesh to clipboard class-----------------------

class MESH_OT_AnimMeshToClipboard(bpy.types.Operator):
    bl_idname = 'animmesh.to_script'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Anim Mesh to Script'
    bl_label = 'Anim Mesh to Script'
    
    def execute(self, context):
            
            current_scene = bpy.context.scene
            
            orig_fps = bpy.data.scenes[current_scene.name].render.fps
            
            if not bpy.context.selected_objects:
                self.report({'ERROR'}, "No object selected")
                return {'CANCELLED'}

                    # Get the active object
            obj = bpy.context.active_object

            # Check if the selected object has any materials
            if not obj.material_slots:
                self.report({'ERROR'}, "No material assigned to the selected object")
                return {'CANCELLED'}
            
            # Check if any material has a Principled BSDF node
            principled_found = False
            for mat_slot in obj.material_slots:
                if mat_slot.material and mat_slot.material.use_nodes:
                    for node in mat_slot.material.node_tree.nodes:
                        if node.type == 'BSDF_PRINCIPLED':
                            principled_found = True
                            break
            
            if not principled_found:
                self.report({'ERROR'}, "Add material with a Principled BSDF node")
                return {'CANCELLED'}

            def urlify(s):

        # Remove all non-word characters (everything except numbers and letters)
                s = re.sub(r"[^\w\s]", '', s)

        # Replace all runs of whitespace with a single dash
                s = re.sub(r"\s+", '_', s)

                return s
            
            # Check if there's a selected object
            obj = bpy.context.active_object
            if obj is None:
                self.report({'ERROR'}, "No object selected")
                return {'CANCELLED'}
            
            
            def checkTex(input_socket):
                """Recursively search for an image texture node starting from the input_socket."""
                if input_socket.is_linked:
                    link = input_socket.links[0]
                    if link.from_node.type == 'TEX_IMAGE':
                        return bpy.path.abspath(link.from_node.image.filepath)
                    else:
                        # Check all input sockets of the linked node recursively
                        for input_socket in link.from_node.inputs:
                            tex_path = checkTex(input_socket)
                            if tex_path is not None:
                                return tex_path
                return None
            
            material_data_list = []

            #check version Blender
            if bpy.app.version[0] >= 5:
                emission = 'Emission Color'
            else:
                emission = 'Emission'

            for slot in obj.material_slots:
                if slot.material:
                    mat = slot.material
                    if mat.use_nodes:
                        for node in mat.node_tree.nodes:
                            if node.type == 'BSDF_PRINCIPLED':
                                material_data = {}            
                                material_data["name"] = urlify(mat.name)
                                material_data["basecolor_tex"] = checkTex(node.inputs['Base Color'])
                                material_data["metallic_tex"] = checkTex(node.inputs['Metallic'])
                                material_data["roughness_tex"] = checkTex(node.inputs['Roughness'])
                                material_data["normal_tex"] = checkTex(node.inputs['Normal'])
                                material_data["emitcolor_tex"] = checkTex(node.inputs[emission])                            
                                material_data["basecolor_r"] = node.inputs['Base Color'].default_value[0]
                                material_data["basecolor_g"] = node.inputs['Base Color'].default_value[1]
                                material_data["basecolor_b"] = node.inputs['Base Color'].default_value[2]
                                material_data["basecolor_a"] = node.inputs['Base Color'].default_value[3]
                                material_data["metallic"] = node.inputs['Metallic'].default_value
                                material_data["roughness"] = node.inputs['Roughness'].default_value
                                material_data["emitcolor_r"] = node.inputs[emission].default_value[0]
                                material_data["emitcolor_g"] = node.inputs[emission].default_value[1]
                                material_data["emitcolor_b"] = node.inputs[emission].default_value[2]
                                material_data["emitcolor_a"] = node.inputs[emission].default_value[3]
                                material_data["emitstrength"] = node.inputs['Emission Strength'].default_value
                                
                                material_data_list.append(material_data)

                    
            dg = bpy.context.evaluated_depsgraph_get()
            
            obj = obj.evaluated_get(dg) #collapse modifiers
            
            obj_data = obj.data
            
            bm = bmesh.new()
            bm.from_mesh(obj_data)
            
            bm.transform(obj.matrix_world)
            
            matrix = axis_conversion(from_forward='-Y', from_up='Z',to_forward='Z',to_up='Y').to_4x4()
            # Use the matrix to transform all vertices
            
            face_vertex_material_ids = []
            num_mats = len(obj.material_slots)

            for face in bm.faces:
                mat_id = face.material_index
                for vertex in face.verts:
                    face_vertex_material_ids.append(mat_id)                 
            
            for vert in bm.verts:
                vert.co = matrix @ vert.co
                vert.normal = matrix.to_3x3() @ vert.normal
            
            animLength = current_scene.frame_end - current_scene.frame_start + 1
            numVerts = len(bm.verts)
            
            textureWidth = math.ceil(math.sqrt(len(bm.verts) * animLength))
                
            verts_coords = np.empty((len(bm.verts), 7), dtype=np.float32)
            anim_coords = np.zeros((textureWidth * textureWidth * 3), dtype=np.float32)
                        
                    
            for i, vert in enumerate(bm.verts):
                verts_coords[i][0] = int(i)
                verts_coords[i][1] = vert.co[0]
                verts_coords[i][2] = vert.co[1]
                verts_coords[i][3] = vert.co[2]
                verts_coords[i][4] = vert.normal[0]
                verts_coords[i][5] = vert.normal[1]
                verts_coords[i][6] = vert.normal[2]  
                                            
            bpy.ops.object.mode_set(mode='OBJECT')

            obj_name = str(obj.name)
            obj_name = urlify(obj_name)
            
            primsDatList = []

            # Get the number of UV channels (which is number of UV layers multiplied by 3)
            uv_channel_count = len(bm.loops.layers.uv) * 3
            
            # Get number of UV layers.
            num_uv_layers = len(bpy.context.object.data.uv_layers)

            # Get active vertex color layer if exists.
            vertex_color_layer = 1 if len(obj_data.vertex_colors) > 0 else 0

            # Check the number of materials.
            num_materials = len(obj_data.materials)

            # Calculate the length of the array for each vertex.
            length = 2 + 3*num_uv_layers + (4 if vertex_color_layer else 0) + (1 if num_materials else 0)

            # Create an empty numpy array with shape (number of loop vertices, calculated length)
            vertsDatList = np.zeros((len(obj_data.loops), length), dtype=np.float32)
                        
            # If the active vertex color layer exists, fetch its name
            if obj_data.vertex_colors:
                active_vc_name = obj_data.vertex_colors.active.name
                vc_layer = bm.loops.layers.color.get(active_vc_name)
            else:
                vc_layer = None
            
            loopCount = 0
            
            for i, face in enumerate(bm.faces):
                vertices_str = ' '.join(str(vertex.index) for vertex in face.verts)
                primsDatList.append([face.index, vertices_str, 1])
                                
                for j, loop in enumerate(face.loops):
                    uv_coords_list = []
                    for uv_layer in bm.loops.layers.uv.values():
                        uv_coords = loop[uv_layer].uv
                        uv_coords_list.extend([uv_coords.x, uv_coords.y, 0.0])  # Appending the UVs and the 0.0 for 'w'

                    # Fetch vertex color data if the layer exists
                    if vertex_color_layer == 1:
                        col = loop[vc_layer]
                        color_data = [col[0], col[1], col[2], col[3]]  # RGBA
                    else:
                        color_data = []
                    
                    loopCount += 1
                    
                    verts_entry = [int(i), int(j)] + uv_coords_list + color_data
                    
                    for idx, value in enumerate(verts_entry):
                        vertsDatList[loopCount -1][idx] = value
                        
                        
            for idx, mat_id in enumerate(face_vertex_material_ids):
                vertsDatList[idx][-1] = mat_id            
            
            verts_coords = verts_coords.tolist()
            vertsDatList = vertsDatList.tolist()
            
            indexCounter = 0

            # Iterate over every animated frame and fill anim_coords
            for f in range(animLength):
                current_scene = bpy.context.scene
                current_scene.frame_set(current_scene.frame_start + f)
                dg = bpy.context.evaluated_depsgraph_get()

                obj = obj.evaluated_get(dg)  # Collapse modifiers

                obj_data = obj.data

                bm = bmesh.new()
                bm.from_mesh(obj_data)

                bm.transform(obj.matrix_world)

                for i, vert in enumerate(bm.verts):
                    vert.co = matrix @ vert.co
                    anim_coords[i * 3 + 0 + indexCounter] = vert.co[0]
                    anim_coords[i * 3 + 1 + indexCounter] = vert.co[1]
                    anim_coords[i * 3 + 2 + indexCounter] = vert.co[2]
                
                indexCounter += len(bm.verts) * 3
                
                bm.clear() 
            
            # Reshape the array
            array_3d = np.reshape(anim_coords, (textureWidth, textureWidth, 3))

            # Convert to list
            anim_coords = array_3d.tolist()
            
                    
    # ---------------------- to Blend2TD format-----------------------

            result = "#BLENDMESHTOTD"
            result += '\nfrom collections import Counter'
            result += '\nimport itertools'
            result += '\nimport numpy as np'
            result += '\npointsDatList = np.array(' + str(verts_coords) + ')'
            result += '\nprimsDatList = ' + str(primsDatList)
            result += '\nvertsDatList = np.array(' + str(vertsDatList) + ')'
            result += '\nanimList = np.array(' +str(anim_coords) + ')'
            result += '\nfps = ' +str(orig_fps)
            result += '\nanimLength = ' +str(animLength)
            result += '\nnumVerts = ' +str(numVerts)
            result += '\nobject_name = ' + "'" +obj_name + "'"
            result += '\nmaterial_list = ' + str(material_data_list)
            result += '\nnum_mats = ' + str(num_mats)
            result += '\nnum_uvs = ' + str(uv_channel_count)
            result += '\nvert_col_num = ' + str(vertex_color_layer)
            result +="""\nfind_datto = parent(2).findChildren(name=object_name)

if len(find_datto) == 0:

    # Create dattoSOP first (not dattoPOP) to properly receive table DAT data
    parent(2).create(dattoSOP, object_name)
    createdSOP = parent(2).op(f'{object_name}')

    createdSOP.nodeX = parent().nodeX + parent().nodeWidth * 1.5
    createdSOP.nodeY = parent().nodeY

    # Create soptoPOP to convert SOP to POP for GPU acceleration
    parent(2).create(soptoPOP, f'{object_name}_POP')
    createdPOP = parent(2).op(f'{object_name}_POP')

    createdPOP.nodeX = createdSOP.nodeX + createdSOP.nodeWidth * 1.5
    createdPOP.nodeY = createdSOP.nodeY

    # Connect dattoSOP to soptoPOP
    createdPOP.par.sop = createdSOP.path

    parent(2).create(nullPOP, f'{object_name}_null')
    createdNull = parent(2).op(f'{object_name}_null')

    createdNull.nodeX = createdPOP.nodeX + createdPOP.nodeWidth * 1.5
    createdNull.nodeY = createdPOP.nodeY

    parent(2).create(geometryCOMP, f'{object_name}_GEO')
    createdGEO = parent(2).op(f'{object_name}_GEO')

    createdGEO.nodeX = createdNull.nodeX + createdNull.nodeWidth * 1.5
    createdGEO.nodeY = createdNull.nodeY

    createdPOP.outputConnectors[0].connect(createdNull)

    createdGEO.create(inPOP, f'{object_name}_in')
    createdIn = parent(2).op(f'{createdGEO.name}/{object_name}_in')
    createdGEO.op('torus1').destroy()


    createdGEO.create(normalPOP, f'{object_name}_normal')
    createdNormal = parent(2).op(f'{createdGEO.name}/{object_name}_normal')
    createdNormal.nodeX = createdIn.nodeX + createdIn.nodeWidth * 1.25
    
    createdGEO.inputConnectors[0].connect(createdNull)
    createdIn.outputConnectors[0].connect(createdNormal)
    
    createdNormal.render = 1
    createdNormal.display = 1
    # Note: normalPOP computes tangents automatically, no parameter needed
    
    createdGEO.create(scriptTOP, f'{object_name}_buffer')
    createdBuffer = parent(2).op(f'{createdGEO.name}/{object_name}_buffer')
    createdBuffer.nodeX = createdNormal.nodeX
    createdBuffer.nodeY = createdNormal.nodeY + createdBuffer.nodeHeight * 1.25
    
    createdGEO.create(nullTOP, f'{object_name}_buffer_null')
    createdBufferNull = parent(2).op(f'{createdGEO.name}/{object_name}_buffer_null')
    createdBufferNull.nodeX = createdNormal.nodeX + createdBuffer.nodeWidth * 1.25
    createdBufferNull.nodeY = createdBuffer.nodeY 
    
    createdBuffer.outputConnectors[0].connect(createdBufferNull)
    
    createdCallbacks = parent(2).op(f'{createdGEO.name}/{object_name}_buffer_callbacks')
    createdCallbacks.destroy()
    
    createdGEO.create(textDAT, f'{object_name}_buffer_callbacks')
    createdCallbacks = parent(2).op(f'{createdGEO.name}/{object_name}_buffer_callbacks')
    createdCallbacks.nodeX = createdNormal.nodeX 
    createdCallbacks.nodeY = createdBuffer.nodeY 
    createdCallbacks.dock = createdBuffer
    createdCallbacks.showDocked = 0
    createdCallbacks.write(f'''import numpy as np
def onCook(scriptOp):
    a = np.array({animList.tolist()}, dtype = 'float32')
    scriptOp.copyNumpyArray(a)''')
    
    
    # if num_mats == 0

    createdGEO.create(lfoCHOP, f'{object_name}_playback')
    createdPlayback = parent(2).op(f'{createdGEO.name}/{object_name}_playback')
    createdPlayback.nodeX = createdBufferNull.nodeX 
    createdPlayback.nodeY = createdBufferNull.nodeY + createdPlayback.nodeHeight * 1.25  
    createdPlayback.par.wavetype = 3
    createdPlayback.par.frequency = 1 / (animLength / fps)

    createdGEO.create(glslMAT, f'{object_name}_glsl')
    createdGLSL = parent(2).op(f'{createdGEO.name}/{object_name}_glsl')
    createdGLSL.nodeX = createdNormal.nodeX + createdNormal.nodeWidth * 1.25

    createdGLSL.par.vec0name = 'uPlayBack'
    createdGLSL.par.vec0valuex.expr = f"op('{createdPlayback.name}')[0]"
    
    createdGLSL.par.vec1name = 'uNumVerts'
    createdGLSL.par.vec1valuex = numVerts
    
    createdGLSL.par.vec2name = 'uNumFrames'
    createdGLSL.par.vec2valuex = animLength

    createdVertex = parent(2).op(f'{createdGEO.name}/{createdGLSL.name}_vertex')
    createdVertex.showDocked = 0
    createdPixel = parent(2).op(f'{createdGEO.name}/{createdGLSL.name}_pixel')
    createdPixel.showDocked = 0

    createdGEO.op(f'{object_name}_glsl_info').showDocked = 0

    parent(2).create(tableDAT, f'{object_name}_points')
    pointsDat = parent(2).op(f'{object_name}_points')
    pointsDat.nodeX = createdSOP.nodeX
    pointsDat.nodeY = createdSOP.nodeY - pointsDat.nodeHeight * 1.5

    pointsDat.dock = createdSOP
    pointsDat.showDocked = 0

    parent(2).create(tableDAT, f'{object_name}_polygons')
    primsDat = parent(2).op(f'{object_name}_polygons')
    primsDat.nodeX = createdSOP.nodeX + primsDat.nodeWidth * 1.5
    primsDat.nodeY = createdSOP.nodeY - primsDat.nodeHeight * 1.5

    primsDat.dock = createdSOP
    primsDat.showDocked = 0

    parent(2).create(tableDAT, f'{object_name}_vertices')
    verticesDat = parent(2).op(f'{object_name}_vertices')
    verticesDat.nodeX = createdSOP.nodeX + verticesDat.nodeWidth * 3
    verticesDat.nodeY = createdSOP.nodeY - verticesDat.nodeHeight * 1.5

    verticesDat.dock = createdSOP
    verticesDat.showDocked = 0
    
        
else:
    createdSOP = parent(2).op(f'{object_name}')
    createdPOP = parent(2).op(f'{object_name}_POP')
    createdNull = parent(2).op(f'{object_name}_null')
    createdGEO = parent(2).op(f'{object_name}_GEO')
    createdIn = parent(2).op(f'{object_name}_GEO/{object_name}_in')
    createdNormal = parent(2).op(f'{object_name}_GEO/{object_name}_normal')
    createdBuffer = parent(2).op(f'{object_name}_GEO/{object_name}_buffer')
    createdBufferNull = parent(2).op(f'{object_name}_GEO/{object_name}_null')
    createdCallbacks = parent(2).op(f'{object_name}_GEO/{object_name}_buffer_callbacks')
    createdPlayback = parent(2).op(f'{object_name}_GEO/{object_name}_playback')
    pointsDat = parent(2).op(f'{object_name}_points')
    primsDat = parent(2).op(f'{object_name}_polygons')
    verticesDat = parent(2).op(f'{object_name}_vertices')
    createdGLSL = parent(2).op(f'{object_name}_GEO/{object_name}_glsl')
    createdVertex = parent(2).op(f'{object_name}_GEO/{object_name}_glsl_vertex')
    createdPixel = parent(2).op(f'{object_name}_GEO/{object_name}_glsl_pixel')    
    
pointsDat.clear()
primsDat.clear()
verticesDat.clear()
createdGEO.destroyCustomPars()

createdVertex.clear()
createdPixel.clear()

parent().store('mat_list', material_list)
parent().store('animated', 1)

# Insert headers FIRST, then append data
pointsDat.insertRow(['index', 'P(0)','P(1)','P(2)','N(0)','N(1)','N(2)'])
for x in pointsDatList:
    pointsDat.appendRow(x)

primsDat.insertRow(['index', 'vertices', 'close'])
for x in primsDatList:
    primsDat.appendRow(x)

# Build vertices header list
verticesDatNameList = []
verticesDatNameList.append('index')
verticesDatNameList.append('vindex')

if num_uvs > 0:
    for x in range(num_uvs):
        verticesDatNameList.append('Tex(' +str(int(x)) + ')')

if vert_col_num > 0:
    for x in range(4):
        verticesDatNameList.append('Color(' + str(int(x)) + ')')

if num_mats > 0:
    verticesDatNameList.append('attrib')

# Insert header FIRST, then append data
verticesDat.insertRow(verticesDatNameList)
for x in vertsDatList:
    verticesDat.appendRow(x)
    
createdSOP.par.pointsdat = str(pointsDat.name)
createdSOP.par.verticesdat = str(verticesDat.name)
createdSOP.par.primsdat = str(primsDat.name)


# write to shader
createdVertex.write(op('vertexShader_anim').text)
parent().WriteToFragment(createdPixel)

createdGEO.par.material = './' + str(createdGLSL.name)

names = [material['name'] for material in material_list]

createdGLSL.par.sampler0.sequence.numBlocks = 1

for id, material in enumerate(names):
    parent().CreateParPage(str(object_name), material, id, id+id)
    
op('offset').par.value0 = 0
op('offset').par.value1 = 0

existingMaterials = createdGEO.findChildren(type=baseCOMP)
compareList = []

for x in existingMaterials:
    compareList.append(x.name)    

destroyList = set(names) ^ set(compareList)

for x in destroyList:
    createdGEO.op(f'{x}').destroy()
    
parent().unstore('*')

"""
            
            bpy.context.window_manager.clipboard = result        
       
            self.report({'INFO'}, "Script copied to Clipboard")
            
            bm.free()
            
            return {'FINISHED'}
    
# ---------------------- end Anim Mesh to clipboard class-----------------------

# ---------------------- Panel draw class-----------------------

# Base panel class for setting space, region, and category
class TDScriptsPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Blend2TD"

# Main panel class with dynamic tabs
class TD_PT_MainPanel(bpy.types.Panel, TDScriptsPanel):
    bl_label = "Blend2TD"
    
    def draw(self, context):
        layout = self.layout
        
        # Export features (Release version - Beta features commented out)
        layout.operator('mesh.to_script', text = 'Mesh', icon = 'OUTLINER_DATA_MESH')
        layout.operator('uvmap.to_script', text = 'UV-Map', icon = 'GROUP_UVS')
        layout.operator('export.to_script', text = 'Material', icon = 'MATERIAL')
        # layout.operator('camera.to_script', text = 'Camera', icon = 'VIEW_CAMERA')
        
        # BETA FEATURES - Commented out for release version
        # layout.separator()
        # layout.label(text="Beta Features:")
        # layout.operator('beta_multi_mat_pop.to_script', text='Export MultiMat POP', icon = 'OBJECT_DATAMODE')
        # layout.operator('animmesh.to_script', text='Export Animated POP', icon = 'OBJECT_DATAMODE')
                

# ---------------------- end Panel draw class-----------------------           


# ---------------------- Registration-----------------------
def register():
    bpy.utils.register_class(VIEW3D_OT_ScriptToClipboard)
    bpy.utils.register_class(CAMERA_OT_CameraToClipboard)
    bpy.utils.register_class(MESH_OT_MeshToClipboard)
    bpy.utils.register_class(UV_OT_UVMapToClipboard)
    bpy.utils.register_class(TD_PT_MainPanel)
    bpy.utils.register_class(BETA_OT_MultiMatPOP)
    bpy.utils.register_class(MESH_OT_AnimMeshToClipboard)


    # BETA FEATURES - Tab system commented out for release version
    # bpy.types.Scene.td_active_tab = bpy.props.EnumProperty(
    # name="Tab",
    # description="Active tab",
    # items=[
    #     ('EXPORT', "Export", "Export related operations"),
    #     # BETA FEATURES - Commented out for release version
    #     # ('BETA', "Beta", "Beta features and settings")
    # ],
    # default='EXPORT'
    # )

def unregister():
    bpy.utils.unregister_class(VIEW3D_OT_ScriptToClipboard)
    bpy.utils.unregister_class(CAMERA_OT_CameraToClipboard)
    bpy.utils.unregister_class(MESH_OT_MeshToClipboard)
    bpy.utils.unregister_class(UV_OT_UVMapToClipboard)
    bpy.utils.unregister_class(TD_PT_MainPanel)
    bpy.utils.unregister_class(BETA_OT_MultiMatPOP)
    bpy.utils.unregister_class(MESH_OT_AnimMeshToClipboard)

if __name__ == "__main__":
    register()    

    
