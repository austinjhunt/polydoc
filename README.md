# polydoc

The following paths have been added to the URLs (both likely temporary) -

/hello - Displays Hello World text
/display_document - Will download a document off of google drive (but right now, it's hard coded to a file ID on Josh's google drive)

## Development

1. [Install Python 3.8](https://www.python.org/downloads/release/python-380/) if you don't already have it installed.
2. Clone this repo to a directory of your liking.

```
cd dev
git clone https://github.com/austinjhunt/polydoc.git

# polydoc

polydoc is a compact Django app for uploading, importing, viewing, annotating, grading and exporting documents (PDFs/images). It provides user auth, a dashboard, Google Drive import/authorization, page-level notes, grading and multi-view document browsing.

Key features
- Document containers (group documents together), create/update/delete, clear and export (summary & detail)
- Upload/import documents (Google Drive integration)
- Document pages viewer with page-level notes and in-place editing
- Document grading and notes saving
- Multiview to browse multiple documents/pages side-by-side
- User auth (login/register/logout), dashboard, privacy policy, and theme toggle

Important routes (high-level)
- /               -> Home
- /login, /register, /logout
- /dash           -> Dashboard
- /drive          -> Drive UI and /drive/authenticate for Drive callback
- /documentcontainer/*  -> create, import-from-drive, update, delete, clear, export
- /document/*     -> create, delete, pages, save-notes, grade, export, clear
- /multiview/<container_id>
- /toggle-theme/   -> AJAX POST to toggle user theme
- /page-notes/<pk>/ -> edit page notes (POST)

Where things live
- App templates: `app/templates/` (index.html, dashboard.html, document_viewer.html, multiview2.html, etc.)
- Static assets: `app/static/` and project `staticfiles/`
- Drive credentials: `drive/credentials.json`

Quick start (local)
1. Create and activate a Python virtualenv (3.8+ recommended).
2. pip install -r requirements.txt
3. python manage.py migrate
4. python manage.py runserver
5. Open http://localhost:8000

Notes
- The app uses pdf2image (Poppler) for rendering PDFs — install Poppler on hosts (or include it in the build for production).
- Google Drive integration requires valid credentials and the Drive token store (see `drive/credentials.json` and `media/drive/tokens/`).
- Run migrations before importing or starting features that reference models.

License / Contributing
- See the project root for contribution notes and dependencies.
