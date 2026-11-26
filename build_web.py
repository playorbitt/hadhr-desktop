"""Assemble web/ for the desktop app from the committed reader in ../qusx.

- The page, its data files, app manifest, service worker and icons come from qusx's latest commit.
- The two word-timing manifests are rewritten to play the bundled recordings
  (audio/alhadr/juz-NN.m4a and audio/para/para-NN.m4a, served by the app itself) instead of
  archive.org, so the app works fully offline.
Usage: python build_web.py"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
QUSX = os.path.join(HERE, "..", "qusx")
WEB = os.path.join(HERE, "web")

def show(path):
    return subprocess.run(["git", "-C", QUSX, "show", f"HEAD:{path}"], capture_output=True, check=True).stdout

shutil.rmtree(WEB, ignore_errors=True)
os.makedirs(os.path.join(WEB, "local_alhadr")); os.makedirs(os.path.join(WEB, "local_para"))
files = subprocess.run(["git", "-C", QUSX, "ls-tree", "--name-only", "HEAD"], capture_output=True, text=True, check=True).stdout.split()
for f in files:
    if f in ("index.html", "manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png") or (f.endswith(".json") and not f.startswith("package")):
        open(os.path.join(WEB, f), "wb").write(show(f))

# Point the reader's internet sources at the app's own mirror (filled by mirror_assets.py), so text,
# mushaf fonts, Arabic fonts and the translation all load offline.
MIRRORS = {
    "https://raw.githubusercontent.com/dfordev1/usxv2/main/output/": "/mirror/usxv2/",
    "https://verses.quran.foundation/fonts/quran/hafs/": "/mirror/qf-fonts/",
    "https://api.alquran.cloud/v1/surah/": "/mirror/alquran/",
}
page = open(os.path.join(WEB, "index.html"), encoding="utf-8").read()
for src, dst in MIRRORS.items():
    assert src in page, f"reader no longer uses {src}: update MIRRORS"
    page = page.replace(src, dst)
gcss = re.search(r'https://fonts\.googleapis\.com/css2\?[^"\']+', page)
if gcss: page = page.replace(gcss.group(0), "/mirror/gfonts/fonts.css")
open(os.path.join(WEB, "index.html"), "w", encoding="utf-8").write(page)
left = sorted(set(re.findall(r"https://(?:raw\.githubusercontent|verses\.quran|api\.alquran|fonts\.g)[^'\"` )]*", page)))
print("internet sources left in the desktop reader:", left or "none")

def offline(path, folder, name):
    m = json.loads(show(path))
    for k in ("audioBase", "audioFallbackBases", "surahAudioBase", "iaItem"):
        m.pop(k, None)
    m["preferLocalAudio"] = True
    local = lambda a: f"audio/{folder}/{name(a)}"
    for t in m["tracks"]:
        t["audio"] = local(t)
    for s in m["surahs"].values():
        for a in s["ayahs"]:
            a["audio"] = local(a)
    return m

alhadr = offline("local_alhadr/manifest.json", "alhadr", lambda a: f"juz-{int(a['juz']):02d}.m4a")
para = offline("local_para/manifest.json", "para", lambda a: f"para-{int(a['juz']):02d}.m4a")
json.dump(alhadr, open(os.path.join(WEB, "local_alhadr", "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(para, open(os.path.join(WEB, "local_para", "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# Every recording the manifests point at must be bundled.
missing = []
for folder, m, src in (("alhadr", alhadr, os.path.join(HERE, "..", "alhadr-m4a")),
                       ("para", para, os.path.join(QUSX, "local_para", "audio"))):
    for t in m["tracks"]:
        f = os.path.join(src, os.path.basename(t["audio"]))
        if not os.path.exists(f): missing.append(f)
print("web/ files:", sorted(os.listdir(WEB)))
print("tracks: Al-Hadr", len(alhadr["tracks"]), "| Para", len(para["tracks"]), "| missing audio:", missing or "none")
