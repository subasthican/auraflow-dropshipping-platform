# AuraFlow apps

The two apps are kept in separate folders:

| Folder | App |
| --- | --- |
| `auraflow-web/` | AuraWeb website, hosted on Vercel. This folder has its own Git repository and deployment setup. |
| `local-app/` | AURAFLOW PRO desktop app, built with Python, Django, and PySide6. |

## Run the local desktop app

- **macOS:** open `local-app/run-scripts/run.command`.
- **Windows:** open `local-app/run-scripts/run.bat`.

For manual setup, open a terminal in `local-app/` and follow [the desktop app README](local-app/README.md).

The desktop app's source code, Python environment (`.venv/`), database, images, and other runtime data (`ApplicationData/`) are all inside `local-app/`. Open that folder in your editor when working on the desktop app; for example, the product dialog is now `local-app/ui/product_detail_dialog.py`.

`edus/` contains unrelated local archives and remains in its original location.
