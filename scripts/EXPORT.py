import os


def relative_path_from_to(path1, path2):
    # Get the relative path
    relative_path = os.path.relpath(path2, path1)
    
    # Replace backward slashes with forward slashes
    relative_path = relative_path.replace("\\", "/")

    # Remove the first '../' from the relative path
    relative_path = relative_path.replace("../", "", 1)
    return relative_path

camPath = "op('{}')".format(relative_path_from_to(str(me.path), str(parent().par.Camera)))

camPath = eval(camPath)

if camPath.type == 'cam':

	camMat = camPath.worldTransform.rows
	
	result = ""
	result += '#TDCAMTOBLEND'
	result += '\nimport bpy'
	result += '\nimport mathutils'
	result += '\nfrom bpy_extras.io_utils import axis_conversion'
	result += '\n\nviewMethod = ' + "'" +str(camPath.par.viewanglemethod) + "'"
	result += '\nfov = ' + str(camPath.par.fov)
	result += '\nfocL = ' + str(camPath.par.focal)
	result += '\naperture = ' + str(camPath.par.aperture)
	result += '\ncamMat = ' + str(camMat)
	result += """\n# Convert your matrix data to a mathutils.Matrix
matrix = mathutils.Matrix(camMat)

conv = axis_conversion(from_forward='Z', from_up='Y',to_forward='-Y',to_up='Z').to_4x4()
matrix = conv @ matrix

# Check if there's an active camera
if bpy.context.scene.camera is None:
    # If not, create a new one
    new_cam = bpy.data.cameras.new('TD_cam')
    new_cam_obj = bpy.data.objects.new('TD_cam', new_cam)
    
    # Link the new camera to the current scene
    bpy.context.scene.collection.objects.link(new_cam_obj)

    # Set the new camera as the active camera
    bpy.context.scene.camera = new_cam_obj
    camera = bpy.context.scene.camera
else:
    # If there's already an active camera, use it
    camera = bpy.context.scene.camera

# Set the camera's matrix
camera.matrix_world = matrix


# Adjust camera settings based on viewMethod
if viewMethod == 'horzfov':
    camera.data.sensor_width = 36
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.data.lens_unit = 'FOV'
    camera.data.angle = math.radians(fov)
elif viewMethod == 'vertfov':
    camera.data.sensor_height = 24
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.lens_unit = 'FOV'
    camera.data.angle = math.radians(fov)
elif viewMethod == 'focalaperture':
    camera.data.lens_unit = 'MILLIMETERS'
    camera.data.sensor_width = aperture
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.data.lens = focL

"""
	
	ui.clipboard = result

else:
	ui.messageBox('Error', 'No camera loaded', buttons=['Ok'])
	