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
```

3. Navigate to the repo and create a Python 3.8 virtual environment to isolate the dependencies for this project.

```
cd polydoc
python3.8 -m venv venv
```

4. Activate the virtual environment and install the project requirements.

```
source venv/bin/activate # (or source venv/Scripts/activate if you're on Windows)
pip install -r requirements.txt
```

5. All Python dependencies are now installed. You should be able to run the development server with the following command:

```
python manage.py runserver
```

6. The application should now be running on port 8000 of localhost. Try opening [http://localhost:8000](http://localhost:8000) in a browser.

## Notes

- Needed to set multiple buildpacks on Heroku to get the PDF2Image library to work. It depends on Poppler, which must be installed and in PATH. Executed the following from Heroku CLI for the library to work in Production. [Documented here](https://stackoverflow.com/questions/63413122/error-while-trying-to-use-pdf2image-on-heroku-libpng12-so-0-cannot-open-share)

```
heroku buildpacks:set heroku/python --app poly-doc
heroku buildpacks:add --index 1 heroku-community/apt --app poly-doc
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt --app poly-doc
```

- Then needed to add an Aptfile to root containing `popplerutils` and `libpng-dev`
- For dev, just needed to install Poppler, e.g. in Ubuntu `sudo apt install poppler-utils`
