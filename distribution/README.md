# Distribution

The distribution layer is responsible for reproducible installation, hardware
capability detection, and conservative runtime/model selection.

Current policy: detect capabilities first; never silently download or replace
a model. Keep setup explicit and local-first.
