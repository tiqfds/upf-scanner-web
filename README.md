# Ultra-processed food scanner (web)

A Python page you can host on your own machine. Submit a photo that shows an ingredient list. The page asks the scanner in the original project, and shows that result. There is no account step, and this page does not classify the list itself.

## Requirements

- The original project next to this folder, at `../Ultra-processed-food`
- That project's Python, which already has the scanner's libraries

If the original project is somewhere else, set `UPF_SCANNER_ROOT` to its folder before starting.

## Host it locally

From this folder:

```bash
..\Ultra-processed-food\apps\Scripts\python.exe server.py
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000).

Choose a photo of the ingredient list, then choose Check this photo. The result stays on the page until you choose Okay.

## What a result means

The card uses the phone's words. A confirmed scan shows Group 1, 2, 3, or 4. An ingredient the scanner has not settled, and that could still be a marker, shows "Likely ultra-processed, being verified." A photo with no readable list asks for another photo and does not show a group. The same is true of a screenshot, a picture with no food, a list that is cut off, and a product that is not a food or a drink. The sentence on the card is the one the scanner already uses.
