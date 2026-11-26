// Hadhr desktop: the QUSX reader in a native window, with every juz (Al-Hadr) and para (Para
// recitation) bundled for offline listening.
//
// A small HTTP server inside the app serves the reader and the audio from the app's resources on
// 127.0.0.1. It answers HTTP range requests, which the reader needs to seek inside a 25-45 minute
// recording exactly (the bundled files are AAC .m4a with the index at the front for that reason).
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::PathBuf;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};
use tower_http::services::ServeDir;

/// Where the reader (web/) and the recordings (audio/alhadr, audio/para) live.
/// HADHR_RESOURCES overrides it during development, so the 1.2 GB of audio need not be copied.
fn resource_root(app: &tauri::App) -> PathBuf {
    if let Ok(dir) = std::env::var("HADHR_RESOURCES") {
        return PathBuf::from(dir);
    }
    app.path().resource_dir().expect("resource directory")
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let root = resource_root(app);
            let web = root.join("web");
            let audio = root.join("audio");
            // Offline copies of the reader's internet sources: QUSX text, mushaf and Arabic fonts, translation.
            let mirror = root.join("mirror");

            // Bind first so the window knows the port; serve on a background runtime.
            let listener = std::net::TcpListener::bind("127.0.0.1:0")?;
            listener.set_nonblocking(true)?;
            let port = listener.local_addr()?.port();
            std::thread::spawn(move || {
                let rt = tokio::runtime::Builder::new_multi_thread()
                    .enable_all()
                    .build()
                    .expect("tokio runtime");
                rt.block_on(async move {
                    let router = axum::Router::new()
                        .nest_service("/audio", ServeDir::new(audio))   // range requests supported
                        .nest_service("/mirror", ServeDir::new(mirror))
                        .fallback_service(ServeDir::new(web));
                    let listener = tokio::net::TcpListener::from_std(listener).expect("listener");
                    axum::serve(listener, router).await.expect("server");
                });
            });

            let url = format!("http://127.0.0.1:{port}/index.html");
            let mut window = WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url.parse().expect("url")))
                .title("Hadhr — Quran")
                .inner_size(1200.0, 820.0)
                .min_inner_size(380.0, 600.0);
            // Opt-in for automated tests only: HADHR_DEBUG_PORT=9333 lets a test browser attach to the
            // app's WebView2 over the DevTools protocol. Unset (normal use) it changes nothing.
            if let Ok(debug_port) = std::env::var("HADHR_DEBUG_PORT") {
                window = window.additional_browser_args(&format!(
                    "--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection --remote-debugging-port={debug_port}"
                ));
            }
            window.build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Hadhr");
}
