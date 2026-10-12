# Original artwork

<!-- cspell:ignore imagegen -->

The AZ-104 website cover was created with the built-in imagegen tool on 2026-10-12. No CLI/API fallback was used. The original image is stored in `docs/site-assets/illustrations/az104-cloud-cover.png` (1902 × 827). The scene is a symbolic teaching illustration rather than a deployed resource topology. Domain and architecture SVGs are original repository-native artwork. Their service icons are symbolic forms drawn in code, not Microsoft logos. The 28 architecture visuals preserve all 259 source nodes, 262 directed connections, and 65 connection labels.

## Supplementary teaching visuals

Thirty-six additional original SVGs live in `docs/site-assets/learning-visuals`.
The 28 lab roadmaps use the exact five task titles, checkpoint IDs, and objective
mappings from each lab's authoritative metadata and instructions. Their arrows
show the exercise sequence, not a resource topology or network traffic.

Five setup illustrations explain Lab 00's toolchain, Azure context, ownership
record, cost and cleanup rehearsal, and readiness report. Three shared guides
illustrate safe execution, evidence-led troubleshooting, and scoped cleanup.
They preserve preview defaults, explicit execution gates, ownership refusal,
and retained or soft-deleted resource reporting. They do not deploy resources.

The two native renderers, `tools/render_learning_visuals.py` and
`tools/render_setup_visuals.py`, reproduce this artwork deterministically and
support `--check`. Every visual includes an accessible name and description;
the website adds alternative text, captions, and full-size links. No additional
raster artwork or image-generation service was used for these SVGs.

## Final cover prompt

```text
Use case: stylized-concept.
Asset type: original wide website and GitHub cover for an AZ-104 Azure Administrator learning environment.
Primary request: a premium illustrated Azure cloud operations world in a BLACK design, matching a polished friendly 3D isometric educational website.
Scene/backdrop: opaque near-black #030712 and deep navy #0B1220, with subtle dark gradient and restrained blue/purple ambient light; no stars or noisy texture. Landscape approximately 2.3:1, generous safe margins.
Subject: a large beautiful cloud at upper center-right, connected by luminous cyan paths to five small rounded floating teaching islands: identity/governance with a person directory card and shield; storage with stacked cylinders and small file boxes; compute with three server racks; networking with linked blue cubes; monitoring/recovery with a heartbeat/chart screen and circular recovery arrow. An open learning book in the foreground connects the scene. Symbolic educational illustration, not a literal deployment diagram. Each subject stays clean and recognizable.
Style/medium: high-quality original 3D isometric editorial illustration, smooth ceramic and glass forms, subtle bevels, precise geometry, beautiful soft reflections, premium tech learning brand.
Color palette: azure blue #0078D4, violet #6366F1, cyan #22D3EE; white/ice-blue highlights, deep navy bases. Controlled glow, bright subjects against a deep black background. Keep shadows visible, no muddy noise.
Composition: connected cloud operations scene fills the central/right two-thirds; left has calm negative space. All illustrations fit in the frame, no cropping. Visually inviting and readable at banner size.
Constraints: no text, no logos, no Microsoft certification badges, no watermarks, no artificial screenshot UI. No people or characters. Original repo-owned artwork. BLACK background must remain dominant.
```
