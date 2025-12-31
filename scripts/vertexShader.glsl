in int attrib;
in vec4 T;

// POP Attributes (explicit declarations for clarity)
in vec3 Tex[1];    // Texture coordinates from dattoPOP
in vec4 Color;     // Vertex color from dattoPOP (optional)

flat out int materialID;

out Vertex
{
	vec4 vertexColor;
	vec3 worldSpacePos;
	mat3 tangentToWorld;
	vec2 texCoord0;
	flat int cameraIndex;
} oVert;

void main()
{
	materialID = attrib;

		gl_PointSize = 1.0;
	{ // Avoid duplicate variable defs
		vec3 texcoord = TDInstanceTexCoord(uv[0]);
		oVert.texCoord0.st = texcoord.st;
	}
	// First deform the vertex and normal
	// TDDeform always returns values in world space
	vec4 worldSpacePos = TDDeform(P);
	vec3 uvUnwrapCoord = TDInstanceTexCoord(TDUVUnwrapCoord());
	gl_Position = TDWorldToProj(worldSpacePos, uvUnwrapCoord);


	// This is here to ensure we only execute lighting etc. code
	// when we need it. If picking is active we don't need lighting, so
	// this entire block of code will be ommited from the compile.
	// The TD_PICKING_ACTIVE define will be set automatically when
	// picking is active.
#ifndef TD_PICKING_ACTIVE

	int cameraIndex = TDCameraIndex();
	oVert.cameraIndex = cameraIndex;
	oVert.worldSpacePos.xyz = worldSpacePos.xyz;
	oVert.vertexColor = TDPointColor();
	vec3 worldSpaceNorm = normalize(TDDeformNorm(N));

	vec3 worldSpaceTangent = TDDeformNorm(T.xyz);
	worldSpaceTangent.xyz = normalize(worldSpaceTangent.xyz);
	// Create the matrix that will convert vectors and positions from
	// tangent space to world space
	// T.w contains the handedness of the tangent
	// It will be used to flip the bi-normal if needed
	oVert.tangentToWorld = TDCreateTBNMatrix(worldSpaceNorm, worldSpaceTangent, T.w);

#else // TD_PICKING_ACTIVE

	// This will automatically write out the nessessary values
	// for this shader to work with picking.
	// See the documentation if you want to write custom values for picking.
	TDWritePickingValues();

#endif // TD_PICKING_ACTIVE
}

