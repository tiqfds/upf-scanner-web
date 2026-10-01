# Ultra-processed food scanner (web)

A web page for checking a food label. You upload a photo of an ingredient list, and the page shows which NOVA group the food falls in (1 to 4), with the ingredients it read.

> **This repository is only the web page.** The scanner that reads the label and decides the group is a separate, private project, and it is not included here. Without it, this repository cannot scan anything: the Streamlit page starts but shows only the message "The scanner package was not found", with no upload form, and the plain Python server exits with the same message. See the demo below for it working.

## Demo

![Uploading a photo of a pasta sauce jar and getting a Group 3 result](docs/demo.gif)

A photo of a pasta sauce jar goes in, and the card shows **Group 3: Processed foods** with the ingredient list. [Watch the full recording](docs/demo.webm) (11 seconds; a live scan can take about 40 seconds).

## What is in this repository

| File | What it does |
|---|---|
| `streamlit_app.py` | The Streamlit page: upload, "Check this photo", the result card, and "Okay" to start over. |
| `server.py` | A plain Python page that does the same job, plus the code both pages share: finding the scanner and running one photo through it. |
| `card.py` | Turns the scanner's answer into the words on the card. It never decides a group. |
| `test_card.py` | Unit tests for `card.py`. They use sample scanner output, so they run without the scanner. |
| `.streamlit/config.toml` | Streamlit settings: local-only address, 20 MB upload limit, colours. |

How one photo moves through it: the page sends the photo to the scanner, the scanner reads the label and returns a result, and `card.py` turns that result into the card. A photo sent here is not saved. There is no account step.

## What a result means

The card uses the phone's words. A confirmed scan shows Group 1, 2, 3, or 4. An ingredient the scanner has not settled, and that could still be a marker, shows "Likely ultra-processed, being verified." A photo with no readable list asks for another photo and does not show a group. The same is true of a screenshot, a picture with no food, a list that is cut off, and a product that is not a food or a drink. The sentence on the card is the one the scanner already uses.

## Run the tests

The tests need only Python:

```bash
python -m unittest test_card
```

## Run it with the scanner

This works only for someone who has the private scanner project. It needs:

- The scanner project next to this folder at `../Ultra-processed-food`, or its folder named in the `UPF_SCANNER_ROOT` environment variable
- That project's Python, which has the scanner's libraries, plus Streamlit (`pip install streamlit`)
- Ollama running with the scanner's vision model
- The scanner's review database running and its credentials set, as the scanner project describes. The page stops at startup if the scanner cannot load its released knowledge base.

From this folder:

```bash
..\Ultra-processed-food\apps\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501). The page listens on this machine only. Choose a photo of the ingredient list, then choose **Check this photo**. The first scan after a break can take a minute while the model loads. The result stays on the page until you choose **Okay**.

The plain Python page does the same job without Streamlit:

```bash
..\Ultra-processed-food\apps\Scripts\python.exe server.py
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000).

### Recording a demo

Open the menu at the top right of the Streamlit page and choose **Record a screencast**. Your browser asks what to share. Pick the tab, scan a photo, then stop the recording and the video downloads. Run one scan first so the model is loaded and the recording is not mostly waiting.
