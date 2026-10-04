# Process

## Tools

I used Codex to inspect the committed Hong Kong Observatory CSV, develop and revise the Python plot, build a month-by-month interactive version, and check the result against the assignment requirements. I wanted a more artistic chart and then asked for a white background and an all-blue scale in which taller marks are darker. For the website, I asked that the circle start empty and reveal a month's bars from their roots when someone hovers nearby. After reviewing a curved-line preview, I chose straight bars and asked Codex to add a Show All option so the whole year can appear at once. I later asked for a separate smooth line connecting the daily bar tips while leaving their measured heights unchanged. I reviewed the generated images and gave feedback on their appearance. Codex used `uv` to run the scripts and the assignment's checker to verify the repository structure.

## Kept

I kept the circular layout with one mark per day. It makes the year feel like a cycle and lets me see rainy clusters and dry stretches at a glance. I also kept month labels and millimetre reference rings so the image remains connected to the data.

## Rejected

I rejected the first straight line chart because it felt too ordinary for the pattern I wanted to show. I also rejected a dark, multicolour version of the rain wheel because the colours distracted from the amount of rain. A white background and a single blue scale make the visual rule clearer: longer and darker means wetter.

During revision, Codex caught a data handling problem: the first circular version silently removed days marked “Trace,” so its supposed 365 days stretched across more than a year. The final script retains trace days as 0.025 mm, within the source's stated range of less than 0.05 mm, and selects 365 calendar days.
