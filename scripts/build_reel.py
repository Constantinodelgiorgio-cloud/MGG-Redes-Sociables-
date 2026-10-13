import subprocess, os, sys

BASE = "/tmp/claude-0/-home-user-MGG-Redes-Sociables-/151d4eb8-7afc-5d6b-be4a-7c903fd3450e/scratchpad/media"
RAW = f"{BASE}/raw"
SEG = f"{BASE}/seg"
os.makedirs(SEG, exist_ok=True)
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT2 = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
BLUE = "0x1093D0"
VOL = 0.35

# (archivo, inicio, duración, líneas de texto, extender_ultimo_cuadro)
SCENES = [
    ("c2_182000.mp4", 1.5, 2.8, ["¿Lo probamos", "en vivo?"], 0),
    ("c1_171301.mp4", 0.5, 3.0, ["Nos recibió", "Pinturas Especiales"], 0),
    ("c7_2951.MOV",   0.0, 3.0, ["Materiales y", "soluciones técnicas"], 0),
    ("c5_174025.mp4", 0.3, 2.8, ["Charla técnica"], 0),
    ("c5_6984.MOV",   0.3, 2.6, ["Conocé. Elegí.", "Proyectá."], 0),
    ("c2_6995.MOV",   0.3, 3.0, ["Demostración", "práctica"], 0),
    ("c2_182027.mp4", 1.0, 2.6, [], 0),
    ("c2_7001.MOV",   0.0, 2.6, ["Calidad que se ve"], 0),
    ("c4_2946.MOV",   0.5, 2.5, ["Un encuentro", "para compartir"], 0),
    ("c6_7019.MOV",   0.0, 1.55, ["¡Gracias a todos", "por venir!"], 1.25),
]

def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")

def text_filters(lines, y0=330, size=82, gap=118, fade=True):
    fs = []
    for i, line in enumerate(lines):
        y = y0 + i * gap
        fs.append(
            f"drawtext=fontfile={FONT}:text='{esc(line)}':fontsize={size}:fontcolor=white:"
            f"box=1:boxcolor={BLUE}@0.92:boxborderw=22:x=(w-text_w)/2:y={y}:"
            + (f"alpha='if(lt(t,0.15),0,if(lt(t,0.4),(t-0.15)/0.25,1))'" if fade else "alpha=1")
        )
    return fs

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); sys.exit(1)

outs = []
for i, (f, ss, d, lines, pad) in enumerate(SCENES):
    out = f"{SEG}/s{i:02d}.mp4"
    total = d + pad
    vf = [
        "scale=1080:1920:force_original_aspect_ratio=increase", "crop=1080:1920",
        "fps=30", "eq=saturation=1.08:contrast=1.04",
    ]
    if pad:
        vf.append(f"tpad=stop_mode=clone:stop_duration={pad}")
    vf += text_filters(lines, fade=(i != 0))
    vf += ["format=yuv420p", "setsar=1"]
    af = (f"aformat=sample_rates=48000:channel_layouts=stereo,volume={VOL},"
          f"apad,atrim=0:{total},afade=t=in:d=0.12,afade=t=out:st={total-0.15}:d=0.15")
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(ss), "-t", str(d), "-i", f"{RAW}/{f}",
         "-map", "0:v:0", "-map", "0:a:0", "-vf", ",".join(vf), "-af", af,
         "-t", str(total), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
    outs.append(out); print("ok", out)

# Placa final: fondo azul, logo blanco, textos
end = f"{SEG}/s99.mp4"
END_D = 3.3
logo = f"{RAW}/logo_img7024.png"
fc = (
    f"color=c={BLUE}:s=1080x1920:r=30:d={END_D}[bg];"
    f"[1:v]scale=1150:-1,crop=1080:ih[lg];"
    f"[bg][lg]overlay=(W-w)/2:(H-h)/2-40,"
    + ",".join(text_filters(["¡Gracias por recibirnos!"], y0=560, size=70))
    + f",drawtext=fontfile={FONT2}:text='{esc('Marmolería Gerónimo Grillo')}':fontsize=54:fontcolor=white:"
      f"x=(w-text_w)/2:y=1330,"
      f"drawtext=fontfile={FONT2}:text='{esc('Consultanos por mensaje directo')}':fontsize=40:fontcolor=white@0.9:"
      f"x=(w-text_w)/2:y=1410,"
      f"fade=t=in:st=0:d=0.35,format=yuv420p,setsar=1[v]"
)
run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
     "-loop", "1", "-i", logo, "-filter_complex", fc, "-map", "[v]", "-map", "0:a",
     "-t", str(END_D), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
     "-c:a", "aac", "-b:a", "192k", end])
outs.append(end); print("ok", end)

lst = f"{SEG}/list.txt"
with open(lst, "w") as fh:
    for o in outs:
        fh.write(f"file '{o}'\n")
final = f"{BASE}/REEL_Charla_PinturasEspeciales.mp4"
run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
     "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-profile:v", "high", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final])
print("FINAL", final)
