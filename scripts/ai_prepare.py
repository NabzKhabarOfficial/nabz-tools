#!/usr/bin/env python3
"""Prepares the AI models for the karaoke tool (runs in GitHub Actions, not on the site).
1) downloads each MDX-Net model with audio-separator and reads its real settings
2) separates a test song with audio-separator (reference) AND with our browser code (assets/karaoke-ai.js via Node)
3) only models where our code matches the reference are published to models/ + models/karaoke-ai.json
Report: models/ai_report.json"""
import json, os, shutil, subprocess, sys, time, traceback

# audio-separator needs ffmpeg; newer GitHub runners no longer ship it
if not shutil.which("ffmpeg"):
    print("ffmpeg missing, installing...", flush=True)
    ok = subprocess.run("sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg", shell=True).returncode == 0
    if not ok or not shutil.which("ffmpeg"):
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "imageio-ffmpeg"], check=True)
        import imageio_ffmpeg
        bindir = "/tmp/ffbin"; os.makedirs(bindir, exist_ok=True)
        dst = os.path.join(bindir, "ffmpeg")
        if not os.path.exists(dst): os.symlink(imageio_ffmpeg.get_ffmpeg_exe(), dst)
        os.environ["PATH"] = bindir + os.pathsep + os.environ.get("PATH", "")
    print("ffmpeg:", shutil.which("ffmpeg"), flush=True)

import numpy as np, soundfile as sf
from audio_separator.separator import Separator

MODELS = [
    ("kara2", "UVR_MDXNET_KARA_2.onnx", "سبک و سریع"),
    ("hq3", "UVR-MDX-NET-Inst_HQ_3.onnx", "کیفیت بالا"),
]
WORK = "/tmp/kai"; MDIR = WORK + "/m"
os.makedirs(MDIR, exist_ok=True); os.makedirs("models", exist_ok=True)

# test song (20 s): singing-like voice in the centre, stereo chords, hats and kick
sr = 44100; n = sr * 20; t = np.arange(n) / sr; rng = np.random.default_rng(7)
notes = rng.integers(0, 8, 80); f0 = 196 * 2 ** (notes[(t * 3).astype(int) % 80] / 12) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t))
ph = np.cumsum(2 * np.pi * f0 / sr)
voc = sum(np.sin(h * ph) / h * (2.0 if 2 < h < 7 else 1.0) for h in range(1, 30)) * np.maximum(0, np.sin(np.pi * t * 1.5)) ** 0.6
voc = np.stack([voc, voc]) * 0.08
inst = np.zeros((2, n))
for i, (f, p) in enumerate([(131, 0.2), (165, 0.8), (196, 0.35), (262, 0.65)]):
    s = sum(np.sin(2 * np.pi * f * k * t + i) / k ** 1.5 for k in range(1, 8)) * 0.03
    inst[0] += s * np.cos(p * np.pi / 2); inst[1] += s * np.sin(p * np.pi / 2)
hat = ((np.arange(n) % 5512) < 500) * rng.standard_normal(n) * 0.04
inst[0] += hat; inst[1] += np.roll(hat, 7)
kick = ((np.arange(n) % 22050) < 4000) * np.sin(2 * np.pi * 55 * t) * np.exp(-(np.arange(n) % 22050) / 900) * 0.35
inst += kick
mix = (voc + inst).astype(np.float32)
sf.write(WORK + "/test.wav", mix.T, sr, subtype="FLOAT")
mix[0].astype("<f4").tofile(WORK + "/test_L.f32"); mix[1].astype("<f4").tofile(WORK + "/test_R.f32")

def si_snr(est, ref):
    est = est.reshape(-1).astype(np.float64); ref = ref.reshape(-1).astype(np.float64)
    a = np.dot(est, ref) / (np.dot(ref, ref) + 1e-12); e = est - a * ref
    return float(10 * np.log10(np.sum((a * ref) ** 2) / (np.sum(e ** 2) + 1e-12)))

report = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "ffmpeg": shutil.which("ffmpeg"), "models": []}
published = []
for mid, fname, label in MODELS:
    info = {"id": mid, "file_name": fname, "label": label}
    try:
        out = f"{WORK}/out_{mid}"; os.makedirs(out, exist_ok=True)
        sep = Separator(output_dir=out, model_file_dir=MDIR, output_format="WAV",
                        mdx_params={"hop_length": 1024, "segment_size": 256, "overlap": 0.25, "batch_size": 1, "enable_denoise": False})
        sep.load_model(model_filename=fname)
        mi = sep.model_instance
        cfg = {"n_fft": int(mi.n_fft), "dim_f": int(mi.dim_f), "dim_t": int(mi.dim_t), "hop": int(mi.hop_length),
               "compensate": float(mi.compensate), "primary": str(mi.primary_stem_name)}
        info.update(cfg)
        files = sep.separate(WORK + "/test.wav")
        paths = [f if os.path.isabs(f) else os.path.join(out, f) for f in files]
        info["ref_files"] = [os.path.basename(p) for p in paths]
        prim = [p for p in paths if f"({cfg['primary']})" in os.path.basename(p)][0]
        ref, _ = sf.read(prim, dtype="float32"); ref = ref.T
        src = getattr(mi, "model_path", None) or os.path.join(MDIR, fname)
        dst = "models/" + fname; shutil.copy(src, dst); info["size"] = os.path.getsize(dst)
        r = subprocess.run(["node", "scripts/ai_test.js", dst, json.dumps(cfg), WORK], capture_output=True, text=True, timeout=5400)
        info["node_log"] = (r.stdout[-800:] + "\n" + r.stderr[-1500:]).strip()
        if r.returncode != 0: raise RuntimeError("node test failed")
        js = json.loads(r.stdout.strip().splitlines()[-1]); info.update(js)
        pL = np.fromfile(WORK + "/js_pL.f32", "<f4"); pR = np.fromfile(WORK + "/js_pR.f32", "<f4")
        m = min(len(pL), ref.shape[1]); jsp = np.stack([pL[:m], pR[:m]])
        info["match_snr_db"] = round(si_snr(jsp, ref[:, :m]), 2)
        instr = "instrument" in cfg["primary"].lower()
        inst_js = jsp if instr else mix[:, :m] - jsp * cfg["compensate"]
        info["inst_sdr_vs_truth_db"] = round(si_snr(inst_js, inst[:, :m]), 2)
        info["ok"] = info["match_snr_db"] >= 20
        if info["ok"]:
            published.append({"id": mid, "label": label, "file": dst, "size": info["size"], "ms_per_chunk_cpu1": info.get("ms_per_chunk"), **cfg})
        else:
            os.remove(dst)
    except Exception as e:
        info["error"] = repr(e); info["trace"] = traceback.format_exc()[-2000:]
    report["models"].append(info)
    print(json.dumps({k: v for k, v in info.items() if k not in ("node_log", "trace")}, ensure_ascii=False), flush=True)

json.dump(report, open("models/ai_report.json", "w"), ensure_ascii=False, indent=1)
if published:
    published.sort(key=lambda x: x["size"])
    json.dump({"version": int(time.time()), "default": published[0]["id"], "models": published}, open("models/karaoke-ai.json", "w"), ensure_ascii=False, indent=1)
    print("published:", [p["id"] for p in published])
else:
    print("::warning::No model passed the test, nothing published. See models/ai_report.json")
