---
name: document-intake-filler
description: Produce a completed form document from structured customer data.
when_to_use: Use when a form file and structured data need to be combined into a checked document.
---

# Document Intake Filler

This package handles form intake jobs where a user supplies a blank document
and machine-readable values.

## Procedure

1. Load the source form file and discover its editable field layout.
2. Check the structured input for all mandatory field keys.
3. Write corresponding values into the document through a form writer.
4. Confirm that mandatory values are present and list any gaps.
5. Export the completed file and return a concise status message.

## Runtime

```python
def render_form_document(template_path, record, destination):
    layout = read_pdf_fields(template_path)
    required_errors = validate_required_fields(layout, record)
    if required_errors:
        raise ValueError({"missing": required_errors})
    form = PdfFormWriter(template_path)
    for key, item in record.items():
        form.set_field(key, item)
    form.save(destination)
    return {"output": destination, "field_count": len(record)}
```

