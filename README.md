# Hadhr — desktop

Read the Quran and follow the recitation word by word, fully offline, on Windows.

A Rust ([Tauri 2](https://tauri.app)) app around the [QUSX reader](https://github.com/playorbitt/qusx)
(also at <https://hadhr.pages.dev>) with everything bundled:

- **Al-Hadr** — all 30 juz, word-by-word timing ([archive.org/details/QuranicRecitationAlHadr](https://archive.org/details/QuranicRecitationAlHadr))
- **Para recitation** — all 30 para, word-by-word timing ([archive.org/details/para-07](https://archive.org/details/para-07))
- QUSX text for all 10 mushaf editions, the mushaf page fonts, Arabic fonts and the English translation

Read / Follow / Explore / Translate views, page arrows and swipe, repeat an ayah, loop a range,
sleep timer, full-screen reading, progress saved per reciter.

## Download

Get the installer from [Releases](https://github.com/playorbitt/hadhr-desktop/releases). It installs for
the current user (no administrator rights) and needs no internet after installing.

## How it works

`src-tauri/src/main.rs` opens a native window and runs a small HTTP server inside the app on
`127.0.0.1`. It serves the reader (`web/`), the recordings (`audio/`) and offline copies of the reader's
online sources (`mirror/`). The server answers HTTP range requests, which the reader needs to seek
inside a 25–45 minute recording exactly; the recordings are AAC `.m4a` with the index at the front
for the same reason (VBR MP3 seeks drifted by seconds).

## Build

Requirements (Windows): [Rust](https://rustup.rs), the Visual Studio C++ Build Tools
(`Desktop development with C++`), Node.js, Python 3, git.

```powershell
git clone https://github.com/playorbitt/qusx ..\qusx          # the reader (sibling folder)
npm install
python mirror_assets.py        # one-time: text, fonts and translation into mirror/ (~300 MB)
npm run build                  # builds web/, compiles the app and packages the NSIS installer
```

The bundle expects the recordings in sibling folders, as in `src-tauri/tauri.conf.json`:
`..\alhadr-m4a\juz-01.m4a … juz-30.m4a` and `..\qusx\local_para\audio\para-01.m4a … para-30.m4a`
(download them from the archive.org items above).

`npm run dev` runs the app without packaging. Set `HADHR_RESOURCES` to a folder holding `web/`,
`audio/` and `mirror/` to skip copying the resources, and `HADHR_DEBUG_PORT` to let automated tests
attach to the window over the DevTools protocol.

## Credits

Quran text and word data: [QUSX](https://github.com/dfordev1/usxv2) · mushaf page fonts:
Quran Foundation / KFGQPC · Arabic fonts: Google Fonts · translation: Pickthall via
[alquran.cloud](https://alquran.cloud) · word timings for the Para recitation and Al-Hadr Juz 24/30:
Quran-Lab Zipformer V3.
