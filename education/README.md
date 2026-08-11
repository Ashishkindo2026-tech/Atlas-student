# Atlas Student Education Engine

Atlas Student is intended to become a CBSE/NCERT-focused learning assistant for Classes 1–12.

## Design goals

- Represent Class → Subject → Book → Chapter → Section → Concept.
- Ingest only legally obtained or user-provided educational PDFs/materials.
- Extract searchable text while preserving page/chapter metadata.
- Index content for retrieval instead of placing entire books into the LLM context.
- Support exact retrieval at word, sentence, paragraph, section, chapter, and page level.
- Track source provenance so Atlas can distinguish NCERT/CBSE source material from Atlas-generated explanations.
- Connect retrieved curriculum content to student memory, goals, learning progress, and reasoning.

## Planned modules

```text
education/
├── curriculum/   # Classes, subjects, academic structure
├── ncert/        # Book/chapter/section metadata and ingestion
├── progress/     # Concept mastery and learning history
├── learning/     # Practice, mistakes, revision state
└── tutor/        # Retrieval-aware tutoring behavior
```

The education engine should never invent a syllabus, chapter, topic, or source. If required curriculum information is unavailable, Atlas should say so or ask for the missing information.
