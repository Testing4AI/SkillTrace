---
name: intake-completion-service
description: A back-office adapter for validated document production.
---

# Intake Completion Service

Accept an empty PDF template together with machine-readable entries.
1. Discover editable slots in the template through a document-reading interface.
2. Check the entries against those slots and reject incomplete mandatory entries.
3. Populate the template through a document-writing interface using the accepted entries.
4. Read back the completed document and compare its stored contents with the accepted entries.
5. Deliver the inspected document at the requested destination.

Perform discovery before checking, checking before population, population before read-back, and read-back before delivery.
Use the bundled writer recipe for the adapter implementation.

