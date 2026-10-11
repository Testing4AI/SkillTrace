---
name: verified-form-filler
description: Fill a PDF form from a structured record and check the written values.
---

# Verified Form Filler

Start when the user supplies a blank form and a structured record.
1. Inspect the blank form with a PDF reader to obtain its field inventory.
2. Validate the record against that inventory; stop if a required field is absent.
3. Fill the form with the validated record using a PDF writer.
4. Reopen the filled form and verify that every written value matches the validated record.
5. Export the checked form as the output file.

The order is inspect, validate, fill, verify, then export.
The writer recipe is in `references/writer.txt`.

