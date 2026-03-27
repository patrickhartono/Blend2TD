# Blend2TD Update Log

## Context
Update Blend2TD add-on: enable beta features (MultiMat POP, Animated Mesh), fix bugs, dan improve pipeline architecture.

---

## Completed

### 1. Bug Fixes di `Blend2TD-Beta_AddOn.py`

| Bug | Fix | Line |
|---|---|---|
| `bm.clear()` crash | Ganti ke `bm.free()` | ~1524 (AnimMesh) |
| `animList.tolist()` not defined in scope | Revert ke `{animList.tolist()}` (variable exist di TD scope) | ~1625 (AnimMesh) |
| `attributecreatePOP` not defined | Removed — TD operator doesn't exist | MultiMatPOP |
| `par.comptang` not on normalPOP | Removed line entirely | MultiMatPOP |
| `par.verticesdat` not on dattoPOP | Switched MultiMatPOP dari dattoPOP ke dattoSOP+soptoPOP | MultiMatPOP |
| `calc_tangents()` error "tris/quads only" | Added bmesh triangulation sebelum calc_tangents() | ~982-987 |
| UV columns `Tex(N)` not recognized by TD | Renamed ke `uv(N)` — TD standard naming | ~1237 |
| `par.int = '*'` casting semua columns ke int (termasuk UV) | Changed ke `par.int = 'index vindex attrib'` | ~1258 |
| `in vec4 Color;` redefinition error di GLSL | Removed — TD sudah punya built-in `Color` | vertexShader.glsl |
| `in vec3 Tex[1]` wrong attribute name di shader | Removed, pakai `uv[0]` standard TD | vertexShader.glsl |

### 2. Architecture Changes di MultiMatPOP

| Perubahan | Dari | Ke |
|---|---|---|
| Pipeline | `dattoSOP → soptoPOP → nullPOP → geometryCOMP(inPOP)` | `dattoSOP → geometryCOMP(inSOP)` |
| Alasan | POP kehilangan vertex attributes (UV, tangent) karena point-based | SOP preserve polygon topology + vertex attributes |

### 3. Mikktspace Tangent Export (MultiMatPOP)
- Added `calc_tangents()` di Blender side
- Export `mesh_loop.tangent` + `mesh_loop.bitangent_sign` per vertex
- Tangent columns: `T(0)`, `T(1)`, `T(2)`, `T(3)` di verticesdat
- `tangent_matrix = matrix.to_3x3() @ obj.matrix_world.to_3x3()` untuk coordinate conversion

### 4. UI Panel
- Uncommented beta feature buttons (MultiMat POP, Animated Mesh)

### 5. Vertex Shader (`scripts/vertexShader.glsl`)
- `in int attrib;` — material ID per face
- `in vec4 T;` — Mikktspace tangent dari dattoSOP
- `uv[0]` — standard TD UV attribute
- Removed POP-specific code (`gl_PointSize`, POP comments)

---

## Discovered Issues (Root Cause Analysis)

### POP tidak bisa untuk textured mesh rendering
- **Root cause**: POP = points only. Tidak punya polygon topology atau vertex (per-loop) attributes.
- **Impact**: `soptoPOP` menghilangkan UV, tangent, dan semua vertex attributes.
- **Conclusion**: Untuk textured polygon rendering, HARUS pakai SOP.

### GLSL MAT unnecessary complexity
- **Root cause**: GLSL MAT dipakai untuk multi-material per mesh via `materialID` di shader.
- **Discovery**: User test PBR MAT bawaan TD — langsung bekerja dengan texture tanpa custom shader.
- **Conclusion**: PBR MAT lebih simple, reliable, dan sudah handle lighting/PBR otomatis.

---

## TODO (Belum Dilakukan)

### Priority 1: Rewrite MultiMatPOP — PBR MAT approach

**Konsep baru:**
- Skip GLSL MAT, pakai PBR MAT bawaan TD
- Single material: `dattoSOP → soptoPOP → geometryCOMP(inPOP + pbrMAT)`
- Multi-material: auto-split mesh per material di Blender, setiap sub-mesh dapat pipeline sendiri

**Blender side:**
- [ ] Auto-split mesh per `material_index` di `execute()`
- [ ] Untuk setiap material: filter faces, collect vertices, re-index
- [ ] Export separate pointsDat/vertsDat/primsDat per material

**TD side (result string):**
- [ ] Untuk setiap material, create:
  - `dattoSOP_{objname}_{matname}`
  - `soptoPOP_{objname}_{matname}`
  - `geometryCOMP_{objname}_{matname}`
    - Inside: `inPOP` (bisa karena PBR MAT handle UV sendiri — PERLU VERIFIKASI)
    - Inside: `pbrMAT` (copy logic dari `VIEW3D_OT_ScriptToClipboard`)
    - Inside: texture TOPs (moviefileinTOP + nullTOP per texture channel)
  - Assign `pbrMAT` ke `geometryCOMP.par.material`
- [ ] Remove semua GLSL-related code (glslMAT, vertex/pixel DAT, custom shaders)
- [ ] Remove dependency ke `td_gen_geo.py` (`CreateParPage`, `WriteToFragment`)

**Perlu diverifikasi:**
- [ ] Apakah `soptoPOP → geometryCOMP(inPOP)` + PBR MAT bisa texture? User claim bisa, tapi perlu confirm karena sebelumnya POP kehilangan UV.
  - Kemungkinan: PBR MAT auto-generate UV dari point positions? Atau user test-nya pakai SOP langsung?
- [ ] Exact PBR MAT parameter names di TD: `par.basecolormap`, `par.normalmap`, `par.metalmap`, `par.roughmap`, `par.emitmap`?

**Reference — existing code yang bisa di-reuse:**
- Material extraction: `VIEW3D_OT_ScriptToClipboard` (lines 36-185) — sudah create pbrMAT + texture TOPs
- Mesh extraction: `MESH_OT_MeshToClipboard` (lines 460-631) — sudah create dattoSOP + soptoPOP + tableDATs

### Priority 2: Animated Mesh Export
- [ ] Test animated mesh export (sudah fix bugs tapi belum di-test)
- [ ] Verify `vertexShader_anim.py` compatibility dengan pipeline baru
- [ ] Kemungkinan juga perlu switch ke PBR MAT approach

### Priority 3: Cleanup
- [ ] Remove `scripts/vertexShader.glsl` dan `scripts/fragmentShader.glsl` jika GLSL MAT sudah tidak dipakai
- [ ] Update `scripts/td_gen_geo.py` — remove `CreateParPage` dan `WriteToFragment` jika sudah tidak dipakai, atau buat method baru untuk PBR MAT
- [ ] Consider: rename operator dari "MultiMatPOP" ke nama yang lebih sesuai

---

## Files Modified

| File | Status |
|---|---|
| `Blend2TD-Beta_AddOn.py` | Modified — bug fixes, pipeline changes, UI enabled |
| `scripts/vertexShader.glsl` | Modified — cleaned up for SOP pipeline |
| `scripts/fragmentShader.glsl` | Unchanged |
| `scripts/IMPORT.py` | Unchanged |
| `scripts/td_gen_geo.py` | Unchanged (will need update for PBR approach) |

---

## Architecture Reference

### Existing Non-Beta Features (Working)
```
Mesh Export:    dattoSOP → soptoPOP (geometry only, no material)
Material Export: pbrMAT + moviefileinTOP + nullTOP (material only, no geometry)
UV Export:      dattoSOP → baseCOMP(inSOP → geometryCOMP) → renderTOP
```

### Target Architecture (MultiMat PBR)
```
Per material:
  dattoSOP_{mat} → soptoPOP_{mat} → geometryCOMP_{mat}
                                       ├─ inPOP
                                       ├─ pbrMAT
                                       └─ [textures folder]
                                            ├─ Basecolormap → null
                                            ├─ Normalmap → null
                                            ├─ Roughnessmap → null
                                            ├─ Metallicmap → null
                                            └─ Emitmap → null
```
