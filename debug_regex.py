import re

text = "A4197/25 NOTAMC A4189/25 \nQ) KZBW/QMNXX////000/999/4305N07049W005 \nA) KPSM\nB) 2512170449\nE)  PSM APRON ALL FICON PATCHY 1/8IN DRY SN OVER COMPACTED SN OBS AT\nCANCELED"

# Updated Regex with * instead of {1,2}
Q_LINE_REGEX = re.compile(
    r"(?:Q\)\s*)?" # Optional Q) prefix
    r"(?P<fir>[A-Z]{4})/"
    r"(?P<code>Q[A-Z]{4})/" # Q-code always starts with Q
    r"(?P<traffic>[IV]*)/" # Relaxed to *
    r"(?P<purpose>[NBOM]*)/" # Relaxed to *
    r"(?P<scope>[AEW]*)/" # Relaxed to *
    r"((?P<lower>[0-9]{3})/(?P<upper>[0-9]{3}))?" # Optional Altitude
    r"(?:/(?P<coords>[0-9]{4}[NS][0-9]{5}[EW]))?" # Optional Coords
    r"(?P<radius>[0-9]{3})?" # Optional Radius
)

cleaned_text = text.replace('\n', ' ').replace('\r', ' ')
print(f"Cleaned Text: '{cleaned_text}'")

match = Q_LINE_REGEX.search(cleaned_text)
if match:
    print("MATCH FOUND!")
    print(match.groupdict())
else:
    print("NO MATCH.")
