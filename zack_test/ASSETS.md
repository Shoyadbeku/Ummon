# Asset manifest

| Asset | Type | Source | License |
|---|---|---|---|
| Megan (`character_refined/Megan.fbx`) | Rigged character, 65-bone Mixamo rig | HF dataset `Linzhan/Mixamo-Animations-Characters` (Adobe Mixamo) | Mixamo terms (royalty-free use in projects; no redistribution of raw files) |
| `Lifting`, `Drinking`, `Focus`, `Dizzy_Idle` (`animation_motion/*.fbx`) | Mocap motions | same dataset | Mixamo terms |
| `street_rat` | Model (glTF 2k) | polyhaven.com/a/street_rat | CC0 |
| `cardboard_box_01`, `worn_metal_rack`, `wooden_crate_02`, `plastic_crate_01` | Props (glTF 2k) | polyhaven.com | CC0 |
| `empty_warehouse_01` | HDRI 2k | polyhaven.com | CC0 |
| `brushed_concrete`, `anti_slip_concrete`, `painted_plaster_wall` | PBR textures 2k | polyhaven.com | CC0 |
| Energy-drink can, cooler, shelves, pallet, Leptospira, organs, liquid | Procedural (Python) | this repo | own work |
| Narration `audio/narration.wav` | Voice | supplied by the user | user's |
| SFX `audio/sfx.wav` | Procedurally synthesised (numpy) | `scripts/sound_design.py` | own work |

Raw Mixamo/Poly Haven files are not committed (`assets/` is git-ignored); `scripts/fetch_assets.py`
re-downloads them. The can design is generic (no real brand).

Not used: the BlenderKit Audi e-tron GT (the story has no car); the
`kloofendal_48d_partly_cloudy_puresky` HDRI was downloaded but the night scenes did not need it.
