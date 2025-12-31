class GenGeo:

	def CreateParPage( self, geo_name, name, id, index):
		
		# id = index of material
		# index = id + id, to give every material 2 slots in the glslMAT
		
		geo = parent(2).op(f'{geo_name}_GEO')
		glsl = geo.op(f'{geo_name}_glsl')
		parameter = parent().fetch('mat_list')
		animated = parent().fetch('animated')
		
		tex_list = [['basecolor_tex', 'Basecolormap', 'Basecolor'], ['metallic_tex', 'Metallicmap', 'Metallic'], ['roughness_tex', 'Roughnessmap', 'Roughness'], ['normal_tex', 'Normalmap', 'Normal'], ['emitcolor_tex', 'Emitmap', 'Emit']]
		color_list = [[f'Basecolor{id}r', 'basecolor_r'], [f'Basecolor{id}g', 'basecolor_g'], [f'Basecolor{id}b', 'basecolor_b'], [f'Basecolor{id}a', 'basecolor_a']]
		emit_list = [[f'Emitcolor{id}r', 'emitcolor_r'], [f'Emitcolor{id}g', 'emitcolor_g'], [f'Emitcolor{id}b', 'emitcolor_b'], [f'Emitcolor{id}a', 'emitcolor_a']]
		
		if not hasattr(geo.par, f'Basecolor{id}r'):

			page = geo.appendCustomPage(name)
			page.appendRGBA('Basecolor' + str(id), label='Basecolor')
			page.appendFloat('Metallic' + str(id), label='Metallic')
			page.appendFloat('Roughness' + str(id), label='Roughness')
			page.appendRGBA('Emitcolor' + str(id), label='Emit')
			
			page.appendTOP('Basecolormap' + str(id), label='Basecolor Map')
			page.appendTOP('Metallicmap' + str(id), label='Metallic Map')
			page.appendTOP('Roughnessmap' + str(id), label='Roughness Map')
			page.appendTOP('Normalmap' + str(id), label='Normal Map')
			page.appendTOP('Emitmap' + str(id), label='Emit Map')
			
		#check if container for texture TOPs exist
		if geo.op(f'{name}'):
			createdCOMP = geo.op(f'{name}')
		else:
			#create container for texture TOPs					
			geo.create(baseCOMP, name)
			createdCOMP = geo.op(f'{name}')
		
		#align material COMPs
		createdCOMP.nodeY = glsl.nodeY
		createdCOMP.nodeX = glsl.nodeX + ((glsl.nodeWidth * 1.5) * op('offset')[0]) + (glsl.nodeWidth * 1.5)
										
		#increment offset for aligning COMP operators in network
		op('offset').par.value0 += 1		
				
		#assign GEO custom pars:
		#basecolor
		for x in color_list:
			setattr(geo.par, x[0], parameter[id][x[1]])
		
		#metallic
		setattr(geo.par, 'Metallic{}'.format(id), parameter[id]['metallic'])
		
		#roughness
		setattr(geo.par, 'Roughness{}'.format(id), parameter[id]['roughness'])
				
		#emit
		for x in emit_list:
			setattr(geo.par, x[0], parameter[id][x[1]] * parameter[id]['emitstrength'])
		
		#assign textures to TOP fields:
		
		offset = 0		
		
		for x in tex_list:			
					
			#check if material container exists					
			if geo.op(f'{name}/{x[1]}') is None:
				#check if to create moviefilein or constant
				if parameter[id][x[0]] is None:
					createdCOMP.create(constantTOP, x[1])
				else:
					createdCOMP.create(moviefileinTOP, x[1])
				
				#aligns TOPs and connect to NULLs
				createdTOP = createdCOMP.op(f'{x[1]}')
				createdTOP.nodeY = createdTOP.nodeHeight * 1.5 * offset
				createdCOMP.create(nullTOP, '{}_null'.format(x[1]))
				createdNULL = createdCOMP.op(f'{x[1]}_null')
				createdNULL.nodeX = createdTOP.nodeX + createdTOP.nodeWidth * 1.5
				createdNULL.nodeY = createdTOP.nodeY
				createdTOP.outputConnectors[0].connect(createdNULL)
									
				#increment offset for aligning TOP operators in network
				offset += 1					
				
			else:
				#create variable to use furtherup
				createdTOP = createdCOMP.op(f'{x[1]}')
											
			if parameter[id][x[0]] is not None:
				#write path to movfiefileinTOPs
				path = './{}/{}_null'.format(name,x[1])
				setattr(geo.par, '{}{}'.format(x[1],id), path)
				file = parameter[id][x[0]]
				createdTOP.par.file = file
			else:
				#write colors to constantTOPs
				createdTOP.par.resolutionw = 1
				createdTOP.par.resolutionh = 1
				if x[0] == 'basecolor_tex':
					createdTOP.par.colorr.expr = f'parent(2).par.Basecolor{id}r' 
					createdTOP.par.colorg.expr = f'parent(2).par.Basecolor{id}g'
					createdTOP.par.colorb.expr = f'parent(2).par.Basecolor{id}b'
					createdTOP.par.alpha.expr = f'parent(2).par.Basecolor{id}a'
				elif x[0] == 'emitcolor_tex':
					createdTOP.par.colorr.expr = f'parent(2).par.Emitcolor{id}r' 
					createdTOP.par.colorg.expr = f'parent(2).par.Emitcolor{id}g'
					createdTOP.par.colorb.expr = f'parent(2).par.Emitcolor{id}b'
					createdTOP.par.alpha.expr = f'parent(2).par.Emitcolor{id}a'
				elif x[0] == 'normal_tex':
					createdTOP.par.colorr = 128/255 
					createdTOP.par.colorg = 128/255
					createdTOP.par.colorb = 1.0
					createdTOP.par.alpha = 1.0
				else:
					createdTOP.par.colorr.expr = f'parent(2).par.{x[2]}{id}'
					createdTOP.par.colorg.expr = f'parent(2).par.{x[2]}{id}'
					createdTOP.par.colorb.expr = f'parent(2).par.{x[2]}{id}'
											
			#create samplers in GLSL MAT			
			sampler_name = f's{x[1]}_{name}'
			top_name = f'{name}/{x[1]}_null'
			setattr(glsl.par, 'sampler{}'.format(int(op('offset')[1])), sampler_name)
			setattr(glsl.par, 'top{}'.format(int(op('offset')[1])), top_name)
			
			#increment offset for adding samplers to GLSL MAT
			op('offset').par.value1 += 1
		
		if animated == 1:
			setattr(glsl.par, 'sampler{}'.format(int(op('offset')[1])), 'sArrayBuffer')
			setattr(glsl.par, 'top{}'.format(int(op('offset')[1])), f'{geo_name}_buffer_null')
		else:
			pass
												
		return
		
	def WriteToFragment(self, target):
		material_list = parent().fetch('mat_list')
		names = [material['name'] for material in material_list]
		for name in names:
			target.write(f'uniform sampler2D sBasecolormap_{name};\nuniform sampler2D sMetallicmap_{name};\nuniform sampler2D sRoughnessmap_{name};\nuniform sampler2D sNormalmap_{name};\nuniform sampler2D sEmitmap_{name};\n')
		
		target.write('\n' + op('fragmentShader').text)
		
		target.write('\nvec4 colors[{}];'.format(len(parent().fetch('mat_list'))))
		
		for id, name in enumerate(names):
			target.write(f'\ncolors[{id}] = createMaterial(sBasecolormap_{name}, sMetallicmap_{name}, sRoughnessmap_{name}, sNormalmap_{name}, sEmitmap_{name});')
		
		target.write('''
		    // Get the color based on the fetched matId value
    		vec4 color = colors[materialID];

    		TDCheckDiscard();
    		TDAlphaTest(color.a);
    		oFragColor = TDOutputSwizzle(color);
			oVertexColor = iVert.vertexColor;
			}
			''')
			
	def AddToFragment(self, id):
		
		#write a function to add samplers and uniforms to the fragment shader
		
		return
		
		
		