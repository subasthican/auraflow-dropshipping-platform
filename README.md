# auraflow-dropshipping-platform

AURAFLOW PRO is an AI-powered dropshipping automation and analytics platform built with Django for data management and PySide6 for a rich desktop UI.

## Features

- Product management with rich image support
- Auto-fill product details from supplier URLs
- Order and shipment tracking
- Marketplace integrations (eBay OAuth flow support)
- Built-in analytics and dashboards
- One-click run scripts for macOS and Windows

## Project Structure

- `main.py`: Desktop app entry point (PySide6 UI)
- `manage.py`: Django management entry point
- `config/`: Django settings and URL configuration
- `core/`: Core models and background scheduler
- `products/`: Product models, services, and UI hooks
- `orders/`: Orders domain models and services
- `shipments/`: Shipment domain models and services
- `analytics/`: Analytics models and services
- `marketplaces/`: Marketplace integration clients
- `ui/`: PySide6 UI components and dialogs
- `run-scripts/`: One-click launchers for macOS and Windows

## Requirements

- Python 3.10+
- macOS or Windows

All Python dependencies are listed in `requirements.txt`.

## Quick Start

### macOS

1. Open `run-scripts/run.command`
2. The script will create a virtual environment, install dependencies, and run the app.

If you see a macOS security prompt, right-click the file and choose Open.

### Windows

1. Open `run-scripts/run.bat`
2. The script will create a virtual environment, install dependencies, and run the app.

## Manual Setup

1. Create a virtual environment
2. Install dependencies from `requirements.txt`
3. Run the app via `main.py`

## Notes

- The UI uses Qt styles; some CSS-like properties may be ignored by Qt on certain platforms.
- If both PySide6 and PyQt6 are installed, you may see warnings about overlapping classes; they are safe to ignore.

## License

Private project. All rights reserved.
