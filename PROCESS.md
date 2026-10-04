# Process

## Tools

I used Codex to inspect the committed Hong Kong Observatory CSV, develop and revise the Python plots, build a month-by-month interactive version, and check the result against the assignment requirements. I began with an ordinary bar chart, then arranged its daily bars in polar coordinates to form a year-long rainfall ring. I wanted a more artistic image, so I asked for a white background and an all-blue scale in which taller bars are darker. For the website, I asked that the circle start empty and reveal a month's bars from their roots when someone hovers nearby. After reviewing a curved-bar preview, I chose straight bars and asked Codex to add a Show All option so the whole year can appear at once.

I then explored turning the bar ring into a line ring. First, I asked Codex to connect the daily bar tips with a smooth line, without changing the bar heights. The overlaid line made the static bar chart too busy, so I removed it from that image and kept the bars as one version. For a separate line-only version, Codex mapped the rainfall values to radial distances and connected the days around the circle. I found the first curve too smooth and asked for more of the daily variation to remain visible, with the end of the year joined to its beginning. Finally, I asked for the space between the inner ring and the closed curve to be filled with a blue gradient that darkens towards higher peaks. The two images show the same year in different ways: bars make individual days clearer, while the continuous shape emphasizes the year's rhythm.

I then asked for a third image that keeps the blue rainfall curve and places a coloured temperature ring inside it, with warmer months in red and cooler months in green. Codex fetched daily mean air temperature from the same Hong Kong Observatory station and averaged it by month over the rainfall chart's exact 365-day period. I kept the monthly numbers and a labelled colour key so the new colours could not be mistaken for rainfall. I reviewed the generated images and gave feedback on their appearance. Codex used `uv` to run the scripts and the assignment's checker to verify the repository structure.

## Kept

I kept the circular layout with one mark per day. It makes the year feel like a cycle and lets me see rainy clusters and dry stretches at a glance. I also kept month labels and millimetre reference rings so the image remains connected to the data.

## Rejected

I rejected the first ordinary bar chart because it felt too conventional for the pattern I wanted to show. I also rejected a dark, multicolour version of the rain wheel because the colours distracted from the amount of rain. A white background and a single blue scale make the visual rule clearer: longer and darker means wetter.

During revision, Codex caught a data handling problem: the first circular version silently removed days marked “Trace,” so its supposed 365 days stretched across more than a year. The final script retains trace days as 0.025 mm, within the source's stated range of less than 0.05 mm, and selects 365 calendar days.
