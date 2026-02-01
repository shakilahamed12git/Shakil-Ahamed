# Convertr — PDF to Word & Document Converter

A modern, responsive file format converter supporting PDF, Word (DOC/DOCX), ODT, RTF, TXT, and HTML.

## Prerequisites

- **Node.js** 18+
- **LibreOffice** (required for conversion)
  - Windows: Install from [libreoffice.org](https://www.libreoffice.org/download/download/) — typically `C:\Program Files\LibreOffice\program\soffice.exe`
  - macOS: `brew install --cask libreoffice` or install from libreoffice.org
  - Linux: `sudo apt install libreoffice` (or equivalent)

## Quick Start

### 1. Install dependencies

```bash
npm run install:deps
```

### 2. Initialize database

```bash
npm run db:setup
```

### 3. Run the app (Python)

```bash
npm run dev
```

Open [http://localhost:3001](http://localhost:3001).

## Features

- **Convert** — PDF ↔ Word, ODT, RTF, TXT, HTML | Word/PPTX to PDF | PPTX to Word | TXT/JPG/PNG to PDF
- **CRUD** — Upload, list, rename, delete files at `/files`
- **Responsive** — Mobile, tablet, desktop
- **Dark theme** — Glassmorphism UI with cyan accents

## Tech Stack

- **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism), JavaScript (ES6+)
- **Backend**: Python 3.11+, FastAPI
- **Conversion**: LibreOffice (headless)
- **Database**: SQLite
