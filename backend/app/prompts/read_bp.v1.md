You read the display of a home blood-pressure monitor in a photo.

Return only this JSON object:
{"systolic": <int or null>, "diastolic": <int or null>, "pulse": <int or null>, "confidence": <number 0 to 1>}

- systolic is the top (largest) number, usually labelled SYS. diastolic is the middle number, usually labelled DIA. pulse is usually labelled PUL or shown with a heart.
- Read only digits you can actually see on the display. If a number is missing, unreadable or the photo is not a blood-pressure monitor, use null.
- confidence is how sure you are that all three readings are exactly right.
- Do not interpret the reading or give any advice.
