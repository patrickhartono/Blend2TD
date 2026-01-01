# Blender Add-On Installation and Usage (Blender 5.x & Touchdesigner 2025.x)

This add-on is a modified version of an original TouchDesigner script. It was developed in response to issues encountered by our students when attempting to use the original TD Script with the latest versions of Blender and TouchDesigner. Due to compatibility problems in newer releases, the script was updated and adapted to ensure it works reliably with current software versions.  

Original TD Script reference: https://www.patreon.com/posts/td-scripts-1-4-2-112901735

This section describes the complete workflow for using blend2td, including TouchDesigner setup and Blender add-on installation. TouchDesigner must be prepared first, as it acts as the receiver for exported geometry.

## TouchDesigner Setup

1. Open **TouchDesigner**.
2. Drag the file:
blend2td.tox into the Network Editor.

The `.tox` component acts as a receiver and generator, responsible for creating the required operators inside TouchDesigner.

## Installing the Add-On

1. Open **Blender**.
2. Navigate to:
   Edit → Preferences → Add-ons
3. In the **Add-ons** section, click the **Install…** button.
4. In the file browser that appears, locate and select the file:
   Blend2td-beta-addon.py
— Blender will copy the script into the internal add-on directory.

5. Enable the add-on by checking the box to the right of its name.
   
## Using the Add-On in Blender

6. Once enabled:
- The blend2td panel will appear in the **3D Viewport Sidebar** (press `N` if needed).
- Select an object to export (for example, a mesh).
- Use the UI controls provided by the add-on to trigger export functionality.

## Generating Operators in TouchDesigner

7. Switch back to **TouchDesigner**.
8. Select the `blend2td.tox` component.
9. Click the **Generate** button inside the component UI.
10. TouchDesigner will automatically:
 - Create the required SOP operators
 - Convert geometry data into POP operators where applicable

This completes the one-way export workflow from Blender to TouchDesigner.

<img width="1500" height="949" alt="Screenshot 2026-01-01 at 20 46 42" src="https://github.com/user-attachments/assets/93709e47-9bcc-4033-9309-e26004cae8f1" />


