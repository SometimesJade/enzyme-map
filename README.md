# EnzymeMap

A Flask web application for finding and visualising restriction enzymes in a
DNA sequence. Given a sequence, EnzymeMap lists the commercial enzymes that
cut it, then draws an interactive **linear** or **circular** restriction map
and a table of the resulting fragments.

---

## Requirements

- **Python 3.11 or newer**
- The packages listed in `requirements.txt` (Flask, Biopython, Plotly)
- An **internet connection** *only* for the GenBank accession option, which
  fetches sequences from NCBI. Pasting a sequence or uploading a file works
  fully offline.

---

## Setup & running

**1. (Recommended)  Using a Pre-Generated PyCharm Flask Project**

Move all unzipped files into the PyCharm Flask Project

**Installing dependencies** 
```bash
pip install -r requirements.txt
```

**Start the application**
```bash
flask --debug run
```
**Open the app**

Visit **http://127.0.0.1:5000** in a web browser.

**Stopping the server**

Press `Ctrl + C` in the terminal.

<br>

**2. Create and activate a virtual environment**

From the project folder (the one containing `app.py`):

Windows (PowerShell):
```powershell
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install the dependencies**
```bash
pip install -r requirements.txt
```

**Start the application**
```bash
python app.py OR flask --debug run
```

**Open the app**

Visit **http://127.0.0.1:5000** in a web browser.

**Stopping the server**

Press `Ctrl + C` in the terminal.

---

## Using the app

The app has three screens that follow on from one another:

1. **Sequence input** — provide a sequence in one of three ways:
   - paste it into the text box (plain or FASTA),
   - upload a `.fasta`, `.fa`, or `.txt` file, or
   - enter a **GenBank accession** (e.g. `NC_005816`).

   Optional settings: mark the sequence as **circular**, restrict analysis to
   a **region** (start / end), and cap the **maximum number of cuts** per
   enzyme.

2. **Enzyme selection** — review the commercial enzymes that cut the sequence
   (with recognition site and cut count) and choose which to map.

3. **Restriction map** — view the interactive linear or circular map plus the
   fragment table. The map can be saved as a **PNG**, and the fragment table
   can be downloaded as a **CSV** (`restriction_fragments.csv`).

---

## Project structure

```
EnzymeMap/
├── app.py                 # Flask routes (input → analysis → map)
├── process_sequence.py    # Input handling, cleaning, validation, enzyme search
├── map_sequence.py        # Cut-site mapping, fragment calculation, Plotly maps
├── requirements.txt       # Python dependencies
├── templates/             # HTML pages
│   ├── sequence_input.html
│   ├── analyse_sequence.html
│   └── map_sequence.html
└── static/
    ├── styles/style.css   # Application styling
    └── js/main.js         # Tab switching, downloads, UI helpers
```

---

## Notes

- Uploads and sequences are limited to roughly **1000 kbp** to keep
  analysis responsive.
- GenBank lookups use NCBI Entrez and may be slower or rate-limited depending
  on network conditions.
