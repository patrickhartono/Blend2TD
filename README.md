# Blend2TD

**Blender → TouchDesigner asset export addon**

A Blender addon that exports 3D assets — meshes, materials, UV maps, and animations — directly into TouchDesigner via a clipboard-based Python script workflow. No intermediate file formats; TD operators are auto-generated from Blender data.

> Based on [Factory Settings TD Scripts v1.4.2](https://github.com/factorysettings/td-scripts), extended and rewritten by Patrick Hartono.

---

## Requirements

| Software | Version |
|---|---|
| Blender | 5.0+ |
| TouchDesigner | 2025.32050+ |

**Dependencies:** NumPy (bundled with Blender — no separate install needed)

---

## Installation

1. In Blender: **Edit → Preferences → Add-ons → Install**
2. Select `Blend2TD-Beta_AddOn.py`
3. Enable the addon (checkbox)
4. The **Blend2TD** panel appears in the 3D View sidebar (press `N` to open)

---

## How It Works

All operators follow the same clipboard-based workflow:

1. Select object(s) in Blender
2. Click the export button in the **Blend2TD** panel
3. A Python script is auto-copied to your clipboard
4. In TouchDesigner: open a **Text DAT**, paste the script, and run it
5. TD operators are created automatically

Textures are not embedded — TD loads them from their original paths on disk.

---

## Features

### Stable

| Button | What it exports | TD result |
|---|---|---|
| **Mesh** | Vertex positions, normals, polygon indices | `dattoSOP` with docked data DATs |
| **Material** | Principled BSDF parameters + texture paths | `pbrMAT` + `moviefileinTOP` / `nullTOP` per channel |
| **UV-Map** | Active UV layer coordinates per vertex loop | UV data table, ready for SOP pipeline |

### Beta (Experimental)

| Button | What it exports | TD result |
|---|---|---|
| **Export MultiMat POP** | Multi-material static mesh, split per material slot | Parent `geometryCOMP` → per-material sub-pipelines with `pbrMAT` |
| **Export Animated POP** | Keyframe mesh deformation + materials, multi-object | Parent `geometryCOMP` → per-material sub-pipelines with `lfoCHOP` + `chopExecuteDAT` animation |

---

## TD Architecture

### MultiMat POP (static mesh, multiple materials)

```
geometryCOMP "ModelName"                    ← parent container
  ├─ dattoSOP_{mat0}                        ← geometry data
  │    └─ (docked tableDATs: points, polygons, vertices)
  ├─ soptoPOP_{mat0}_POP
  ├─ geometryCOMP_{mat0}_GEO               ← renders sub-mesh
  │    ├─ inPOP
  │    └─ pbrMAT + texture TOPs
  └─ ... (repeated per material slot)
```

### AnimMesh (animated mesh deformation)

```
geometryCOMP "ModelName"                    ← parent container
  ├─ dattoSOP_{mat0}                        ← geometry data
  │    └─ (docked tableDATs: points, polygons, vertices)
  ├─ soptoPOP_{mat0}_POP
  ├─ geometryCOMP_{mat0}_GEO               ← renders sub-mesh
  │    ├─ inPOP
  │    ├─ pbrMAT + texture TOPs
  │    ├─ lfoCHOP (sawtooth playback)
  │    └─ chopExecuteDAT (updates P(0)/P(1)/P(2) per frame)
  └─ ... (repeated per material slot)
```

Both operators mirror the hierarchy of TD's native FBX `fileinCOMP` — move/rotate/scale the parent container and all children follow.

---

## Usage Notes

- **Mesh:** Select any mesh object before exporting
- **Material:** Active object must have a **Principled BSDF** material node
- **UV-Map:** Object must have at least one UV map; the active UV layer is exported
- **MultiMat POP:** Object must have multiple material slots assigned to faces
- **AnimMesh:** Respects the scene frame range (`Start` / `End`); supports multi-object selection (select all mesh objects to export, with one active object)

---

## Known Limitations

- **AnimMesh performance:** Vertex positions are updated via a Python loop in `chopExecuteDAT` — O(n_verts) per frame. High-polygon models will be slow. GPU texture-based animation is planned but not yet implemented.
- **Texture paths:** Absolute file paths are used. If you move texture files after exporting, TD won't find them.
- **Materials:** Only **Principled BSDF** nodes are supported. Custom node setups are not parsed.
- **Deformation only:** AnimMesh captures vertex position changes per frame (shape deformation / morph). Skeletal/armature animation is not supported.

---

## File Structure

```
Blend2TD/
├── Blend2TD-Beta_AddOn.py    # Main addon — all operators and UI panel
├── scripts/
│   ├── EXPORT.py             # Camera export helper (TD-side script)
│   ├── IMPORT.py             # TD clipboard integration helper
│   ├── td_gen_geo.py         # Legacy helper (unused since PBR MAT rewrite)
│   ├── vertexShader.glsl     # Legacy GLSL (unused)
│   ├── fragmentShader.glsl   # Legacy GLSL (unused)
│   └── vertexShader_anim.py  # Legacy animation shader (unused)
├── Blend2TD.tox              # TouchDesigner template file
└── log.md                    # Development changelog (detailed)
```

---

## Changelog

See [log.md](log.md) for a full development log including architecture decisions, bug fixes, and known issues.
