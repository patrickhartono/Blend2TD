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

### 6. Rewrite MultiMatPOP → PBR MAT approach

**Blender side:**
- Auto-split mesh per `material_index` — each material gets its own sub-mesh
- Filter faces, collect unique vertices, re-index from 0 per material
- Export separate pointsDat/vertsDat/primsDat per material
- Removed `calc_tangents()`, tangent export, vertex color export, material ID attribute
- Simplified vertsDatList columns to `[index, vindex, uv(0), uv(1)]`

**TD side:**
- Per material creates: `dattoSOP → soptoPOP → geometryCOMP(inPOP + pbrMAT + texture TOPs)`
- PBR MAT params: `basecolorr/g/b`, `metallic`, `roughness`, `emitr/g/b`, texture maps via `moviefileinTOP → nullTOP`
- Removed all GLSL-related code: `glslMAT`, vertex/pixel shader DATs, `CreateParPage()`, `WriteToFragment()`, `store()`/`unstore()`
- Auto-cleanup stale operators from previous exports
- Naming: `{objectname}_{materialname}_{slotindex}` for disambiguation

**Architecture:**
```
Per material:
  dattoSOP_{obj}_{mat}_{idx} → soptoPOP_{obj}_{mat}_{idx}_POP → geometryCOMP_{obj}_{mat}_{idx}_GEO
                                                                    ├─ inPOP
                                                                    ├─ pbrMAT (assigned to geometryCOMP.par.material)
                                                                    └─ texture TOPs per channel
                                                                         moviefileinTOP → nullTOP
```

### 7. Rewrite AnimMesh → PBR MAT approach

**Blender side:**
- Same per-material split as MultiMatPOP
- Collect animation positions per frame for all vertices
- Map animation data through per-material vertex re-indexing (old_to_new)

**TD side:**
- Same pipeline as MultiMatPOP: `dattoSOP → soptoPOP → geometryCOMP(inPOP + pbrMAT + texture TOPs)`
- Animation via `lfoCHOP` (sawtooth playback) + `chopExecuteDAT` that updates pointsDat P(0),P(1),P(2) each frame
- Animation frames stored in `dattoSOP.store('anim_frames', ...)`
- Removed GLSL MAT, custom shaders, `CreateParPage`, `WriteToFragment`, `store`/`unstore` dependencies

**Architecture:**
```
Per material:
  dattoSOP → soptoPOP → geometryCOMP
                           ├─ inPOP
                           ├─ pbrMAT + texture TOPs
                           ├─ lfoCHOP (playback)
                           └─ chopExecuteDAT (updates pointsDat per frame)
```

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

### ~~Priority 1: Rewrite MultiMatPOP — PBR MAT approach~~ ✅ DONE

### ~~Priority 2: Animated Mesh Export~~ ✅ DONE

### Priority 3: Cleanup
- [ ] Remove `scripts/vertexShader.glsl` dan `scripts/fragmentShader.glsl` — GLSL MAT sudah tidak dipakai
- [ ] Remove `scripts/vertexShader_anim.py` — tidak dipakai lagi
- [ ] Remove `scripts/fragmentShader.glsl` — tidak dipakai lagi
- [ ] Update `scripts/td_gen_geo.py` — `CreateParPage` dan `WriteToFragment` sudah tidak dipakai, bisa di-remove
- [ ] Consider: rename operator dari "MultiMatPOP" dan "AnimMesh" ke nama yang lebih sesuai

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
