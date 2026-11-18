# "Kalamush zahri bankada" — 3D short (Blender 5.2, Cycles)

Vertical 9:16 short (1080×1920, 24 fps, 43.7 s) with Uzbek narration: rats run over energy-drink
cans in the warehouse at night, and when the can is opened the tab pushes *Leptospira* bacteria
into the drink. Final video: `output/final_video.mp4`.

## Storyboard (approved)

| Shot | Timecode | Frames | Visual action | Camera | Animation | Lighting | Transition |
|---|---|---|---|---|---|---|---|
| 1 HOOK | 0:00.0–0:06.3 | 1–151 | Megan takes a cold can from the open cooler (fridge-cam), cracks it, brings it to her lips | 1a 18 mm fridge-cam from inside the cooler → 1a2 24 mm low-angle push-in → 1b 70 mm macro riding on the can → 1c 50 mm f/2 push-in | Mixamo `Lifting` → `Drinking` (NLA), procedural tab | Cold cooler LEDs + warm ceiling panels | Whoosh on every cut |
| 1b STING | 0:06.3–0:09.3 | 152–223 | Macro of the can rim, a rat rises behind it in red light | 28→85 mm crash zoom, rack focus | Procedural rat | Red backdrop, rim lights | Impact + squeak, whip |
| 2 WIDE | 0:09.3–0:15.4 | 224–369 | Dark warehouse, can pallet, moonbeam; the rat appears on the pallet | 24 mm dolly + descent | Procedural gallop | Moonlight through the window, volumetric fog, HDRI `empty_warehouse_01` | Whoosh |
| 3 LOW-ANGLE ACTION | 0:15.4–0:25.0 | 370–600 | The rat runs over the can tops at the lens, stops at the lid, sniffs; a drop falls on the lid | 3a 20 mm at can height → 3b 50 mm side orbit → 3c 85 mm macro | `street_rat` + procedural run/sniff, drop anim | Cold key + warm rim | Cut on the drop impact |
| 4 UV REVEAL | 0:25.0–0:27.9 | 601–669 | The lid looks clean, but under a UV lamp the dried trace glows | 85 mm f/2 push-in | UV sweep, emission mask | Violet spotlight | Hum, cut |
| 5 PAYOFF | 0:27.9–0:37.7 | 670–905 | 5a: tab opens in slow motion, bacteria sit on the panel → 5b: can cutaway, spiral bacteria fall into the drink | 100 mm macro → 60 mm cutaway, dive into the liquid | Procedural tab/flap, Leptospira helices (corkscrew spin), bubbles | Studio rim lights, back-lit amber liquid | Fizz, plops |
| 6 FINAL | 0:37.7–0:43.7 | 906–1049 | Megan grabs her head (headache) → X-ray: liver and kidneys pulse red and go out | 6a 70 mm f/1.8 low close-up → 6b 35 mm orbit | `Focus` → `Dizzy_Idle` | Harsh cold key, dimmed store | Heartbeat slows and stops |

Creative assumptions: the rat is Poly Haven's static model with procedural motion (no rig);
the bacteria are magnified for an explainer effect; the organs are a stylised X-ray.

## Reproduction
See `CLAUDE.md` (pipeline commands, technical pitfalls). Assets are fetched by
`scripts/fetch_assets.py`; the manifest and licences are in `ASSETS.md`.
