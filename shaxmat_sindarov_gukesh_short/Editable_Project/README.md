# Editable_Project (Short 9:16)

Qayta render: `cd prod && python3 music.py . 34 && ./mix.sh /path/to/audio.mp3 mix.wav && for i in 0 1 2 3; do python3 render.py part$i.mp4 $((i*249)) $(( (i+1)*249 )) & done; wait` keyin part fayllarini concat qilib mix.wav bilan birlashtiring (to‘liq buyruq: ../../shaxmat_sindarov_gukesh_video/Editable_Project/README.md).
Sahnalar: `render.py` ichidagi oxirgi `build()` (9:16).
