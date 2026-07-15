---
name: pdf-form-helper
description: Fill PDF forms from a structured JSON record and verify the output.
when_to_use: Use when a user provides a blank PDF form and wants a validated filled copy.
---

# PDF Form Helper

Use this skill when the user has a blank form document and a JSON record.

## Workflow

1. Read the blank PDF document and inspect the form field structure.
2. Validate the JSON input against the required field names.
3. Fill matching fields in the PDF using the document writer.
4. Verify that required fields were written and report missing values.
5. Save the filled document and provide a short completion summary.

## Implementation

```python
def fill_pdf_form(pdf_path, payload, output_path):
    fields = read_pdf_fields(pdf_path)
    missing = validate_required_fields(fields, payload)
    if missing:
        raise ValueError({"missing": missing})
    writer = PdfFormWriter(pdf_path)
    for name, value in payload.items():
        writer.set_field(name, value)
    writer.save(output_path)
    return {"output": output_path, "field_count": len(payload)}
```

