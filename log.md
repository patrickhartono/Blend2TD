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

### 8. Multi-Object Export (AnimMesh)
- AnimMesh now loops over all selected mesh objects (`bpy.context.selected_objects` filtered to `MESH` type)
- Each object's mesh is split per material, animation frames collected per object
- Animation data mapped to per-material sub-meshes via `old_to_new` vertex re-indexing
- TD script uses `obj_name` from each mat entry for pipeline naming: `{obj_name}_{mat_name}_{mat_idx}`

### 9. Parent geometryCOMP Container (MultiMatPOP + AnimMesh)
- Both operators now create a single parent `geometryCOMP` as container
- All per-material pipelines (dattoSOP, soptoPOP, child geometryCOMPs) created **inside** the container
- Mirrors how TD's FBX `fileinCOMP` structures imported models
- Transform inheritance: move/rotate/scale parent = all children follow
- Container named after object (MultiMatPOP) or active object (AnimMesh)

**Architecture (current):**
```
geometryCOMP "ModelName"                    ← parent container
  ├─ dattoSOP_{mat0}                        ← inside container
  │    └─ (docked tableDATs: points, polygons, vertices)
  ├─ soptoPOP_{mat0}_POP
  ├─ geometryCOMP_{mat0}_GEO               ← child, renders sub-mesh
  │    ├─ inPOP
  │    ├─ pbrMAT + texture TOPs
  │    └─ lfoCHOP + chopExecuteDAT (AnimMesh only)
  ├─ dattoSOP_{mat1}
  ├─ soptoPOP_{mat1}_POP
  ├─ geometryCOMP_{mat1}_GEO
  │    └─ ...
  └─ ...
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

### Performance issue: AnimMesh sangat slow di TouchDesigner
- **Symptom**: Setelah export animated multi-object model, TD menjadi sangat lambat (tested on MacBook Pro 64GB RAM)
- **Likely root cause**: `chopExecuteDAT` updates pointsDat per-vertex per-frame via Python loop — ini sangat lambat untuk high-poly models. Setiap frame, Python iterates semua vertices dan updates table cells satu per satu.
- **Potential solutions**:
  - [ ] Gunakan texture-based animation (scriptTOP + numpy buffer) instead of per-cell table update
  - [ ] Batch update pointsDat via numpy array assignment instead of cell-by-cell loop
  - [ ] Reduce animation data precision (float16 instead of float32)
  - [ ] Consider CHOP-based animation pipeline instead of Python script

---

## TODO (Belum Dilakukan)

### ~~Priority 1: Rewrite MultiMatPOP — PBR MAT approach~~ ✅ DONE

### ~~Priority 2: Animated Mesh Export~~ ✅ DONE

### ~~Priority 3: Multi-Object Export~~ ✅ DONE

### ~~Priority 4: Parent Container COMP~~ ✅ DONE

### Priority 5: Performance — AnimMesh playback optimization
- [ ] Investigate texture-based vertex animation (GPU-side) vs current Python table update (CPU-side)
- [ ] Profile chopExecuteDAT bottleneck — per-vertex Python loop is O(n) per frame
- [ ] Consider GLSL vertex shader approach for animation deformation (texture lookup in shader)

### Priority 6: Cleanup
- [ ] Remove `scripts/vertexShader.glsl` dan `scripts/fragmentShader.glsl` — GLSL MAT sudah tidak dipakai
- [ ] Remove `scripts/vertexShader_anim.py` — tidak dipakai lagi
- [ ] Remove `scripts/fragmentShader.glsl` — tidak dipakai lagi
- [ ] Update `scripts/td_gen_geo.py` — `CreateParPage` dan `WriteToFragment` sudah tidak dipakai, bisa di-remove
- [ ] Consider: rename operator dari "MultiMatPOP" dan "AnimMesh" ke nama yang lebih sesuai

---

## Files Modified

| File | Status |
|---|---|
| `Blend2TD-Beta_AddOn.py` | Modified — bug fixes, pipeline rewrites, multi-object, container COMP |
| `scripts/vertexShader.glsl` | Modified — cleaned up for SOP pipeline (now unused) |
| `scripts/fragmentShader.glsl` | Unchanged (now unused) |
| `scripts/IMPORT.py` | Unchanged |
| `scripts/td_gen_geo.py` | Unchanged (now unused) |

---

## Architecture Reference

### Existing Non-Beta Features (Working)
```
Mesh Export:    dattoSOP → soptoPOP (geometry only, no material)
Material Export: pbrMAT + moviefileinTOP + nullTOP (material only, no geometry)
UV Export:      dattoSOP → baseCOMP(inSOP → geometryCOMP) → renderTOP
```

### Current Architecture (MultiMat + AnimMesh)
```
geometryCOMP "ModelName" (parent container)
  Per material:
    dattoSOP_{mat} → soptoPOP_{mat} → geometryCOMP_{mat}
                                         ├─ inPOP
                                         ├─ pbrMAT
                                         ├─ [texture TOPs per channel]
                                         │    moviefileinTOP → nullTOP
                                         └─ [AnimMesh only]
                                              lfoCHOP → chopExecuteDAT
```
