layout(location = 0) out vec4 oFragColor;
layout(location = 1) out vec4 oVertexColor;

flat in int materialID;

in Vertex
{
	vec4 vertexColor;
	vec3 worldSpacePos;
	mat3 tangentToWorld;
	vec2 texCoord0;
	flat int cameraIndex;
} iVert;

vec4 createMaterial(sampler2D inputBaseColor, sampler2D inputMetallic, 
					sampler2D inputRoughness, sampler2D inputNormal,
					sampler2D inputEmit){

	float uBumpScale = 1.0;
	float uAlphaFront = 1.0;
	vec3 uBaseColor = vec3(1.0);
	float uSpecularLevel = 1.0;
	float uMetallic = 1.0;
	float uRoughness = 1.0;
	float uAmbientOcclusion = 1.0;
	vec3 uShadowColor = vec3(0.0);
	float uShadowStrength = 1.0;
	vec3 uEmission = vec3(1.0);
	
	// This allows things such as order independent transparency
	// and Dual-Paraboloid rendering to work properly
	TDCheckDiscard();

	// This will hold the combined color value of all light sources
	vec3 lightingColor = vec3(0.0, 0.0, 0.0);
	vec3 diffuseSum = vec3(0.0, 0.0, 0.0);
	vec3 specularSum = vec3(0.0, 0.0, 0.0);

	vec2 texCoord0 = iVert.texCoord0.st;
	vec4 normalMap = texture(inputNormal, texCoord0.st);
	vec3 worldSpaceNorm = iVert.tangentToWorld[2];
	vec3 norm = (2.0 * (normalMap.xyz - 0.5)).xyz;
	norm.xy = norm.xy * uBumpScale;
	norm = iVert.tangentToWorld * norm;
	vec3 normal = normalize(norm);
	vec3 viewVec = normalize(uTDMats[iVert.cameraIndex].camInverse[3].xyz - iVert.worldSpacePos.xyz );

	//vec4 color = TDColor(iVert.color);

 
	// Alpha Calculation
	float alpha = uAlphaFront;


	vec3 baseColor = uBaseColor.rgb;

	// 0.08 is the value for dielectric specular that
	// Substance Designer uses for it's top-end.
	float specularLevel = 0.08 * uSpecularLevel;
	float metallic = uMetallic;

	float roughness = uRoughness;

	float ambientOcclusion = uAmbientOcclusion;

	vec4 finalBaseColor = vec4(baseColor.rgb * alpha, alpha);

 	vec4 baseColorMap = texture(inputBaseColor, texCoord0.st);
	finalBaseColor *= baseColorMap;

	float mappingFactor = 1.0f;

	vec4 metallicMapColor = texture(inputMetallic, texCoord0.st);
	mappingFactor = metallicMapColor.r;
	metallic *= mappingFactor;

	vec4 roughnessMapColor = texture(inputRoughness, texCoord0.st);
	mappingFactor = roughnessMapColor.r;
	roughness *= mappingFactor;


	// A roughness of exactly 0 is not allowed
	roughness = max(roughness, 0.0001);

	vec3 pbrDiffuseColor = finalBaseColor.rgb * (1.0 - metallic);
	vec3 pbrSpecularColor = mix(vec3(specularLevel), finalBaseColor.rgb, metallic);

	alpha = finalBaseColor.a;

	// Flip the normals on backfaces
	// On most GPUs this function just return gl_FrontFacing.
	// However, some Intel GPUs on macOS have broken gl_FrontFacing behavior.
	// When one of those GPUs is detected, an alternative way
	// of determing front-facing is done using the position
	// and normal for this pixel.
	if (!TDFrontFacing(iVert.worldSpacePos.xyz, worldSpaceNorm.xyz))
	{
		normal = -normal;
	}

	// Your shader will be recompiled based on the number
	// of lights in your scene, so this continues to work
	// even if you change your lighting setup after the shader
	// has been exported from the Phong MAT
	for (int i = 0; i < TD_NUM_LIGHTS; i++)
	{
		TDPBRResult res;
		res = TDLightingPBR(
							i,
							pbrDiffuseColor,
							pbrSpecularColor,
							iVert.worldSpacePos.xyz,
							normal,
							uShadowStrength, uShadowColor,
							viewVec,
							roughness);
		diffuseSum += res.diffuse;
		specularSum += res.specular;
	}

	// Environment lights
	for (int i = 0; i < TD_NUM_ENV_LIGHTS; i++)
	{
		TDPBRResult res;
		res = TDEnvLightingPBR(
					i,
					pbrDiffuseColor,
					pbrSpecularColor,
					normal,
					viewVec,
					roughness,
					ambientOcclusion);
		diffuseSum += res.diffuse;
		specularSum += res.specular;
	}
	// Final Diffuse Contribution
	vec3 finalDiffuse = diffuseSum;
	lightingColor += finalDiffuse;

	// Final Specular Contribution
	vec3 finalSpecular = vec3(0.0);
	finalSpecular += specularSum;

	lightingColor += finalSpecular;

	vec4 emitMapColor = texture(inputEmit, texCoord0.st);

	// Emission Contribution, treated like a fake light
	lightingColor += uEmission * emitMapColor.rgb;

	vec4 finalColor = vec4(lightingColor, alpha);

	// Apply fog, this does nothing if fog is disabled
	finalColor = TDFog(finalColor, iVert.worldSpacePos.xyz, iVert.cameraIndex);

	// Dithering, does nothing if dithering is disabled
	finalColor = TDDither(finalColor);


	// Modern GL removed the implicit alpha test, so we need to apply
	// it manually here. This function does nothing if alpha test is disabled.
	TDAlphaTest(finalColor.a);

	
	return finalColor;
}


void main()
{
