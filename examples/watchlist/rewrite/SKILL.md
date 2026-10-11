---
name: instrument-sentinel
description: A compact instrument briefing and saved-rule notification assistant.
---

# Instrument Sentinel

On a briefing request, choose the processing profile for the requested ticker.
The regular profile queries a headline provider, whereas the minimal profile omits that lookup.
On a notification request, first restore the persistent tracking list and its rules from the local store.
Next, evaluate those rules against the latest quotations through the monitoring interface to obtain notification findings.
Return the notification findings.
Restore before evaluation; evaluation precedes returning findings.

