# Enterprise UX Rule

Whenever a new field is introduced, the AI must evaluate:

1. Is this field truly necessary?
2. Can this value be automatically derived?
3. Can it be fetched from another DocType?
4. Can it be calculated instead of entered?
5. Can it have a sensible default?
6. Should it be read-only?
7. Will asking for this information slow down the user?

If the answer to questions 2–6 is "yes", the field should not require manual user input.
