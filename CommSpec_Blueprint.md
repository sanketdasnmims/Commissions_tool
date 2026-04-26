# CommSpec — Requirements & Test Creation Tool for SAP Commissions
## Enterprise Blueprint v1.0

---

# SECTION 1 — PRODUCT REQUIREMENTS DOCUMENT

## 1.1 Product Summary

CommSpec is an AI-assisted, human-governed requirements and test creation platform purpose-built for SAP Commissions landscapes. It ingests unstructured and structured enterprise artifacts, extracts and normalizes requirements, routes them through a human approval gate, and generates implementation-ready, traceable QA test assets.

It is not a generic AI document tool. Every extraction, inference, and test case is anchored in SAP Commissions domain logic.

## 1.2 Problem Statement

Enterprise SAP Commissions implementations suffer from:
- Requirements scattered across emails, Confluence pages, chat logs, design docs, and verbal agreements
- Implicit business logic that never gets written down until defects surface
- Test cases written from memory rather than from approved requirements
- No traceability between business intent and QA coverage
- Repeated scope interpretation failures between business, functional, and technical teams
- Inaccurate requirements that survive review because reviewers cannot quickly compare them against source evidence

CommSpec eliminates these failure modes.

## 1.3 Users

| Role | What They Do in CommSpec |
|---|---|
| Business Analyst | Uploads source material, reviews extracted requirements, approves or edits drafts |
| SAP Commissions Functional Consultant | Validates domain logic accuracy, tags components, resolves open questions |
| QA Lead | Reviews generated test cases, exports to test management tool, assigns to testers |
| Project Manager | Monitors approval pipeline, tracks coverage gaps, reviews traceability matrix |
| Solution Architect | Reviews architecture implications, flags integration risks |
| Business Stakeholder | Read-only view of approved requirements, approval signoff |

## 1.4 Core Workflows

**Workflow A: New Requirement from Raw Sources**
Upload sources → Auto-classify → Extract candidates → Compose draft → Human review → Approve → Generate tests → Export

**Workflow B: Requirement Update from Change Request**
New source contradicts approved requirement → System flags conflict → Re-review triggered → Version bump → Regenerate affected tests

**Workflow C: Gap Analysis**
Upload all available project artifacts → System surfaces missing requirements, untested acceptance criteria, orphan test cases

## 1.5 Success Criteria

- A BA can produce an approval-ready requirement from raw source material in under 30 minutes
- A QA lead can produce a full test set for an approved requirement without writing test steps from scratch
- Every approved requirement has a minimum traceability score (all sections populated, all acceptance criteria testable)
- No test case exists without an approved requirement behind it
- Every requirement clause cites at least one source evidence snippet

## 1.6 Non-Functional Requirements

| Concern | Requirement |
|---|---|
| Response time | Extraction on a 50-page PDF completes within 90 seconds |
| Concurrent users | Supports 20 concurrent active sessions |
| Data residency | Configurable — EU, US, or on-premise AI inference option |
| Security | Role-based access, audit log for all mutations, no source data sent to AI without consent flag |
| Export | Test cases exportable to XLSX, JSON, and ALM/Zephyr-compatible format |
| Explainability | Every AI inference cites the source snippet it came from |

---

# SECTION 2 — SYSTEM ARCHITECTURE

## 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  Intake │ Extraction Workspace │ Requirement Review │ Test View  │
│  Traceability Matrix │ Approval Console │ Audit History          │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS / REST + WebSocket
┌────────────────────────▼────────────────────────────────────────┐
│                     API LAYER (FastAPI)                          │
│  intake/ │ extraction/ │ requirements/ │ approval/               │
│  testgen/ │ traceability/ │ export/ │ admin/                     │
└──────┬──────────┬──────────────┬──────────────┬─────────────────┘
       │          │              │              │
┌──────▼──┐  ┌────▼────┐  ┌─────▼─────┐  ┌────▼────────────────┐
│ PostgreSQL│  │  Redis  │  │  Celery   │  │   AI Reasoning      │
│ + pgvector│  │ (cache/ │  │  Workers  │  │   Layer (Claude)    │
│ (primary  │  │  queue) │  │  (async   │  │   - Extraction      │
│  store)   │  │         │  │   tasks)  │  │   - Composition     │
└──────────┘  └─────────┘  └───────────┘  │   - Test Gen        │
                                           │   - Conflict Detect │
┌──────────────────────┐                   └────────────────────┘
│  File Storage         │
│  (Azure Blob / S3)    │
│  Raw uploaded files   │
└──────────────────────┘
```

## 2.2 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Next.js 14 (TypeScript) | SSR for heavy document views, strong typing, rich ecosystem |
| UI Components | Tailwind CSS + shadcn/ui | Professional, accessible, enterprise-appropriate |
| Rich Text Editing | TipTap | Requirement editing with structured blocks |
| Table/Matrix | TanStack Table | Traceability matrix with sorting, filtering, pinning |
| State Management | Zustand | Lightweight, sufficient for this use case |
| Backend API | FastAPI (Python 3.12) | Async, typed, Python AI ecosystem, OpenAPI docs auto-generated |
| ORM | SQLAlchemy 2.0 + Alembic | Migrations, type-safe queries |
| Primary Database | PostgreSQL 16 + pgvector | Relational data + semantic vector search in one system |
| Task Queue | Celery + Redis | Document processing is slow — must be async |
| File Storage | Azure Blob Storage (or S3) | Enterprise default, configurable |
| AI | Anthropic Claude API | claude-opus-4-6 for reasoning, claude-haiku-4-5 for classification |
| Auth | Auth0 or Entra ID | Enterprise SSO, MFA, role claims |
| Containerisation | Docker + Docker Compose | Local dev parity; K8s manifests for production |

## 2.3 Repository Structure

```
commspec/
├── apps/
│   ├── web/                          # Next.js frontend
│   │   └── src/
│   │       ├── features/
│   │       │   ├── intake/           # Upload, classify sources
│   │       │   ├── extraction/       # Review extracted candidates
│   │       │   ├── requirements/     # Compose, review, edit requirements
│   │       │   ├── approval/         # Approval console and history
│   │       │   ├── testgen/          # Test case viewer and export
│   │       │   └── traceability/     # Matrix and lineage views
│   │       └── shared/
│   │           ├── components/       # Reusable UI blocks
│   │           ├── hooks/
│   │           ├── lib/              # API client, formatters
│   │           └── types/            # Shared TypeScript types
│   │
│   └── api/                          # FastAPI backend
│       └── app/
│           ├── features/
│           │   ├── intake/
│           │   │   ├── router.py
│           │   │   ├── service.py
│           │   │   ├── repository.py
│           │   │   └── schemas.py
│           │   ├── extraction/
│           │   ├── requirements/
│           │   ├── approval/
│           │   ├── testgen/
│           │   └── traceability/
│           ├── shared/
│           │   ├── ai/
│           │   │   ├── prompts/      # All prompt templates
│           │   │   └── client.py     # Anthropic client wrapper
│           │   ├── db/               # Session, base model
│           │   ├── queue/            # Celery app, task definitions
│           │   └── storage/          # File storage abstraction
│           ├── main.py
│           └── config.py
│
├── packages/
│   └── types/                        # Shared contract types (if TypeScript shared)
│
├── db/
│   ├── migrations/                   # Alembic migration files
│   └── seeds/                        # Demo/test seed data
│
├── docs/
│   ├── architecture/
│   └── api/
│
└── scripts/
    ├── dev-setup.sh
    └── seed-demo.py
```

## 2.4 Why This Stack Is Clean

- Business logic never lives in route handlers — all routes call a service, which calls a repository
- AI calls are isolated inside `shared/ai/` — no feature module imports the Anthropic SDK directly
- File storage is abstracted behind an interface — swap Azure for S3 without touching feature code
- Async document processing via Celery means the API never blocks on a 60-second extraction job
- pgvector removes the need for a separate vector database for semantic source search at this scale

---

# SECTION 3 — UI MODULE BREAKDOWN

## Screen 1: Source Intake Dashboard

**Purpose:** Central hub showing all ingested sources for a project.

**Components:**
- Project selector (top bar)
- Source list table: filename, type, date, author, component tags, confidence, status
- Upload zone: drag-drop, multi-file, paste text
- Batch import button (ZIP of artifacts)
- Filter bar: type, component, date range, status
- Staleness indicator: sources older than configurable threshold flagged amber
- Duplicate detection banner: "3 documents appear to contain overlapping content"

**Actions:**
- Upload → triggers async classification job, shows progress
- Click source → open Source Review screen
- Tag manually → domain/component tags
- Mark as superseded → removes from active extraction pool

---

## Screen 2: Source Review / Classification Screen

**Purpose:** Review a single source, validate auto-classification, and view extracted snippets.

**Components:**
- Document viewer (PDF render or formatted text)
- Side panel: auto-assigned metadata (type, author, date, component tags, confidence)
- Extracted snippets panel: highlights in document, listed in side panel
- Snippet actions: accept, reject, re-tag, add note
- Conflict flag viewer: "This snippet conflicts with [Source B, snippet 14]"
- Domain tag editor

---

## Screen 3: Requirement Discovery Workspace

**Purpose:** Review all extracted requirement candidates for a given topic/component before composition.

**Components:**
- Candidate list: extracted statements grouped by component
- Per-candidate: text, source citation, confidence score, domain tag, status (included/excluded/pending)
- Conflict panel: side-by-side conflicting statements with source metadata
- Gap indicators: "No acceptance criteria found for this candidate"
- Open questions list: surfaced by AI, editable
- "Compose Requirement" button → triggers composition

---

## Screen 4: Requirement Draft Review Screen

**Purpose:** Review the AI-composed requirement draft before routing to approval.

**Components:**
- Structured requirement form (all fields, see data model)
- Per-field source citation links: hover/click to see evidence snippet
- Confidence indicator per section: High / Medium / Low / Inferred
- Assumption list with "Accept" checkboxes
- Open question list with assignment and status
- Diff view when editing (show what changed from last version)
- "Submit for Approval" button
- "Request AI Refinement" button with instruction field

---

## Screen 5: Approval Console

**Purpose:** Human reviewer approves, edits, comments on, or rejects a requirement.

**Components:**
- Requirement read-only view (full structured display)
- Status banner: Draft / Under Review / Approved / Rejected / Superseded
- Comment thread per section
- Overall comment box
- Approve / Request Changes / Reject buttons
- Approval history log: who, what, when
- Version selector: compare v1 vs v2

**Hard rule enforced in UI:** "Generate Tests" button is disabled and hidden until status = Approved.

---

## Screen 6: Test Case Generation Screen

**Purpose:** View, edit, and export generated test cases for an approved requirement.

**Components:**
- Requirement summary bar (ID, title, component, approval date)
- Test scenario list: grouped by scenario
- Per-test-case: full structured view (see data model)
- Test type filter: Positive / Negative / Boundary / Exception / Security / Integration / Data
- Coverage indicators: which acceptance criteria are covered vs uncovered
- Export button: XLSX, JSON, ALM format
- "Regenerate" button (with confirmation) — re-runs AI on approved requirement

---

## Screen 7: Traceability Matrix View

**Purpose:** End-to-end lineage from source to requirement to test case.

**Components:**
- Matrix table: rows = requirements, columns = source snippets + test cases
- Colour coding: linked (green), partial (amber), orphan (red)
- Orphan requirement list: approved requirements with no test coverage
- Orphan test list: tests with no clear requirement anchor
- Export matrix to XLSX
- Filter by component, status, domain

---

## Screen 8: Audit / Version History Screen

**Purpose:** Full immutable log of all actions on a requirement.

**Components:**
- Timeline view: all events in order
- Event types: created, extracted from source, edited, submitted, approved, rejected, test generated, superseded
- Actor, timestamp, and changed fields for each event
- Side-by-side diff viewer for any two versions
- Restore to version (creates new version, does not delete history)

---

# SECTION 4 — BACKEND SERVICE BREAKDOWN

## 4.1 intake.service

Responsibilities:
- Receive uploaded files and pasted content
- Detect file type and route to appropriate parser (PDF, DOCX, XLSX, TXT, JSON)
- Chunk content into semantic segments
- Run auto-classification via AI (type, author, date, component tags, confidence)
- Store chunks with embeddings in pgvector
- Deduplicate near-duplicate content using cosine similarity threshold
- Flag stale documents based on date metadata

Key methods:
- `ingest_file(file, project_id, metadata) → SourceDocument`
- `ingest_text(text, metadata) → SourceDocument`
- `classify_source(doc_id) → ClassificationResult`
- `detect_duplicates(doc_id) → list[DuplicateCandidate]`

---

## 4.2 extraction.service

Responsibilities:
- Read all accepted source chunks for a given scope (project, component, topic)
- Extract atomic requirement candidates: rules, actors, triggers, data fields, validations, exceptions
- Score confidence per candidate
- Detect contradictions between candidates from different sources
- Surface missing information (gaps in acceptance criteria, undefined actors, missing exception flows)
- Normalize domain terminology

Key methods:
- `extract_candidates(scope) → list[RequirementCandidate]`
- `detect_conflicts(candidates) → list[ConflictFlag]`
- `surface_gaps(candidates) → list[GapIndicator]`
- `normalize_terms(candidates) → list[RequirementCandidate]`

---

## 4.3 requirements.service

Responsibilities:
- Compose a structured requirement draft from accepted candidates
- Maintain version history
- Handle edit/update/refinement cycles
- Calculate requirement quality score (completeness, testability)
- Flag weak requirements

Key methods:
- `compose_requirement(candidates, project_id) → Requirement`
- `update_requirement(req_id, changes, actor) → RequirementVersion`
- `score_requirement(req_id) → QualityScore`
- `refine_requirement(req_id, instruction) → Requirement`

---

## 4.4 approval.service

Responsibilities:
- Manage requirement lifecycle state machine
- Record approval actions with actor and timestamp
- Enforce hard gate: test generation cannot be triggered on non-approved requirements
- Notify relevant users on state transition
- Compute delta between versions for review

Key methods:
- `submit_for_review(req_id, actor) → ApprovalRecord`
- `approve(req_id, actor, comment) → ApprovalRecord`
- `reject(req_id, actor, comment) → ApprovalRecord`
- `request_changes(req_id, actor, comments) → ApprovalRecord`
- `get_version_diff(req_id, v1, v2) → RequirementDiff`

State machine:
```
DRAFT → UNDER_REVIEW → APPROVED
                     → REJECTED → DRAFT
APPROVED → SUPERSEDED (when new version approved)
```

---

## 4.5 testgen.service

Responsibilities:
- Accept only approved requirements as input (enforced at service layer, not just UI)
- Generate test scenarios and test cases using AI
- Ensure coverage across all test types
- Validate coverage against acceptance criteria
- Flag acceptance criteria with no test coverage

Key methods:
- `generate_tests(req_id) → list[TestScenario]`
- `validate_coverage(req_id) → CoverageReport`
- `regenerate_tests(req_id, actor) → list[TestScenario]`

Enforcement:
```python
def generate_tests(req_id):
    req = requirement_repo.get(req_id)
    if req.status != RequirementStatus.APPROVED:
        raise TestGenerationBlockedError("Requirement must be approved before test generation.")
```

---

## 4.6 traceability.service

Responsibilities:
- Maintain links between source snippets, requirement clauses, and test cases
- Compute traceability coverage metrics
- Detect orphan requirements and orphan tests
- Revalidate traceability when new sources are added that conflict with existing approved requirements

Key methods:
- `build_traceability_matrix(project_id) → TraceabilityMatrix`
- `get_orphan_requirements(project_id) → list[Requirement]`
- `get_orphan_tests(project_id) → list[TestCase]`
- `revalidate_on_new_source(source_id) → list[RequirementConflict]`

---

## 4.7 export.service

Responsibilities:
- Export test cases to XLSX (structured, human-readable)
- Export to JSON (for ALM tool ingestion)
- Export traceability matrix to XLSX

---

# SECTION 5 — DATA MODEL

## Core Entities

### SourceDocument
```
id                  UUID PK
project_id          UUID FK
filename            TEXT
source_type         ENUM (BRD, FDD, TDD, UserStory, ProcessDoc, MeetingNotes, Email, Chat, TestScript, DefectLog, IntegrationSpec, ConfigWorkbook, ReleaseNotes, SOP, Other)
raw_content_path    TEXT  -- path in blob storage
parsed_text         TEXT
author              TEXT
document_date       DATE
ingested_at         TIMESTAMP
ingested_by         UUID FK (User)
classification_confidence  DECIMAL
is_stale            BOOLEAN
superseded_by       UUID FK (SourceDocument) NULLABLE
tags                JSONB  -- domain/component tags
metadata            JSONB  -- flexible capture of additional metadata
```

### SourceChunk
```
id                  UUID PK
source_document_id  UUID FK
chunk_index         INT
text                TEXT
embedding           VECTOR(1536)  -- pgvector
char_start          INT
char_end            INT
component_tags      TEXT[]
confidence          DECIMAL
```

### SourceSnippet
```
id                  UUID PK
chunk_id            UUID FK
source_document_id  UUID FK
text                TEXT
relevance_reason    TEXT
component_tag       TEXT
extracted_at        TIMESTAMP
status              ENUM (ACCEPTED, REJECTED, PENDING)
```

### RequirementCandidate
```
id                  UUID PK
project_id          UUID FK
source_snippet_id   UUID FK
statement           TEXT
candidate_type      ENUM (RULE, ACTOR, TRIGGER, VALIDATION, EXCEPTION, DATA_FIELD, INTEGRATION, REPORTING, SECURITY, NON_FUNCTIONAL)
component           ENUM (Workflow, BTP_EDL, ICM_Engine, Embedded_Analytics, Integration, Participants, Credit, Incentive, Territory, Payee_Hierarchy, Batch, Security, Other)
confidence          DECIMAL
status              ENUM (INCLUDED, EXCLUDED, PENDING)
conflict_flag_id    UUID FK NULLABLE
```

### Requirement
```
id                  UUID PK
project_id          UUID FK
requirement_id_display  TEXT  -- e.g. REQ-WF-001
title               TEXT
status              ENUM (DRAFT, UNDER_REVIEW, APPROVED, REJECTED, SUPERSEDED)
component           ENUM
current_version_id  UUID FK
created_at          TIMESTAMP
created_by          UUID FK
```

### RequirementVersion
```
id                  UUID PK
requirement_id      UUID FK
version_number      INT
business_objective  TEXT
in_scope            TEXT
out_of_scope        TEXT
background          TEXT
actors              JSONB  -- list of {role, description}
preconditions       TEXT[]
trigger             TEXT
main_flow           JSONB  -- ordered steps
alternate_flows     JSONB
exception_flows     JSONB
business_rules      TEXT[]
data_requirements   JSONB
integration_touchpoints JSONB
reporting_needs     TEXT
security_implications TEXT
audit_implications  TEXT
non_functional_reqs JSONB
assumptions         JSONB  -- list of {text, accepted_by, accepted_at}
open_questions      JSONB  -- list of {text, owner, status, resolution}
acceptance_criteria JSONB  -- list of {id, text, testable_flag}
dependencies        TEXT[]
risks               JSONB
quality_score       DECIMAL
created_at          TIMESTAMP
created_by          UUID FK
change_summary      TEXT
```

### ApprovalRecord
```
id                  UUID PK
requirement_id      UUID FK
requirement_version_id UUID FK
action              ENUM (SUBMITTED, APPROVED, REJECTED, CHANGES_REQUESTED)
actor_id            UUID FK
timestamp           TIMESTAMP
comment             TEXT
```

### TestScenario
```
id                  UUID PK
scenario_id_display TEXT  -- e.g. TS-WF-001
requirement_id      UUID FK
requirement_version_id UUID FK
title               TEXT
objective           TEXT
component           ENUM
generated_at        TIMESTAMP
generated_by        TEXT  -- "AI" or user ID
status              ENUM (DRAFT, REVIEWED, APPROVED, DEPRECATED)
```

### TestCase
```
id                  UUID PK
case_id_display     TEXT  -- e.g. TC-WF-001-01
scenario_id         UUID FK
requirement_id      UUID FK
acceptance_criterion_id TEXT  -- links to acceptance_criteria[].id in RequirementVersion
title               TEXT
test_type           ENUM (POSITIVE, NEGATIVE, BOUNDARY, EXCEPTION, SECURITY, INTEGRATION, DATA_VALIDATION, WORKFLOW, REGRESSION)
objective           TEXT
preconditions       TEXT[]
test_data_requirements TEXT
steps               JSONB  -- list of {step_num, action, expected_result}
expected_result     TEXT
postconditions      TEXT
component           ENUM
priority            ENUM (CRITICAL, HIGH, MEDIUM, LOW)
execution_notes     TEXT
```

### TraceabilityLink
```
id                  UUID PK
source_type         ENUM (SNIPPET_TO_CANDIDATE, CANDIDATE_TO_REQUIREMENT, REQUIREMENT_TO_TESTCASE, SNIPPET_TO_REQUIREMENT)
source_id           UUID
target_id           UUID
link_type           TEXT
confidence          DECIMAL
created_at          TIMESTAMP
```

### ConflictFlag
```
id                  UUID PK
project_id          UUID FK
snippet_a_id        UUID FK
snippet_b_id        UUID FK
conflict_description TEXT
severity            ENUM (CRITICAL, MAJOR, MINOR)
resolution_status   ENUM (OPEN, RESOLVED, ACCEPTED_AS_IS, DEFERRED)
resolution_note     TEXT
resolved_by         UUID FK NULLABLE
resolved_at         TIMESTAMP NULLABLE
```

### AuditLog
```
id                  UUID PK
project_id          UUID FK
entity_type         TEXT  -- Requirement, TestCase, SourceDocument, etc.
entity_id           UUID
action              TEXT
actor_id            UUID FK
timestamp           TIMESTAMP
before_state        JSONB
after_state         JSONB
```

---

# SECTION 6 — WORKFLOW & ORCHESTRATION DESIGN

## Full Workflow

```
1. INGEST
   User uploads files / pastes text
   → intake.service: parse, chunk, embed
   → Async Celery task: classify_source
   → Store in SourceDocument + SourceChunk
   → Deduplication check
   → Return: source classified, ready for extraction

2. CLASSIFY (async, background)
   Claude prompt: classify this document
   → Set source_type, component_tags, confidence, is_stale flag
   → Embed all chunks via pgvector

3. EXTRACT (user-triggered per scope)
   User selects scope (project + component)
   → extraction.service reads all accepted chunks
   → Claude prompt: extract requirement candidates
   → Conflict detection: cosine similarity + Claude comparison
   → Gap detection: Claude prompt
   → Store RequirementCandidates, ConflictFlags
   → Return: candidates ready for composition

4. COMPOSE (user-triggered)
   User reviews candidates, includes/excludes
   → requirements.service: compose_requirement
   → Claude prompt: produce structured requirement from accepted candidates
   → Quality score computed
   → RequirementVersion v1 created, status = DRAFT

5. REVIEW CYCLE (human-driven, iterative)
   User edits requirement directly or requests AI refinement
   → Each edit creates new RequirementVersion
   → Diff computed between versions
   → User submits for approval: status → UNDER_REVIEW

6. APPROVE (human gate)
   Reviewer approves, rejects, or requests changes
   → On APPROVED: status → APPROVED, approval record created
   → On REJECTED: status → REJECTED, returns to DRAFT
   → On CHANGES_REQUESTED: returns to DRAFT, comments attached

7. GENERATE TESTS (only after APPROVED)
   → testgen.service checks status (hard gate)
   → Claude prompt: generate test assets from approved requirement
   → Coverage validation against acceptance criteria
   → TraceabilityLinks created
   → TestScenarios and TestCases stored

8. REVALIDATION (triggered by new source)
   New source uploaded that semantically conflicts with approved requirement
   → traceability.service detects via embedding similarity
   → ConflictFlag raised against approved requirement
   → Notification to requirement owner
   → Human decision: accept conflict or trigger requirement revision
   → If revision: new RequirementVersion, existing version → SUPERSEDED
```

## State Machine: Requirement

```
DRAFT
  ↓ submit_for_review()
UNDER_REVIEW
  ↓ approve()                ↓ reject()         ↓ request_changes()
APPROVED                   REJECTED              DRAFT (with comments)
  ↓ new version approved
SUPERSEDED
```

## State Machine: TestCase

```
DRAFT (auto-generated)
  ↓ reviewed by QA lead
REVIEWED
  ↓ approved for execution
APPROVED
  ↓ if requirement superseded
DEPRECATED
```

---

# SECTION 7 — AI PROMPT STRATEGY

## Design Principles

1. Every prompt specifies the SAP Commissions domain context
2. Every output demands source citation — no inference without evidence
3. Confidence levels are explicit in every extraction response
4. Contradictions are surfaced, not silently resolved
5. Claude is instructed to say "insufficient information" rather than hallucinate
6. All prompts use structured JSON output for reliable parsing

---

## Prompt 1: Source Classification

```
You are an expert SAP Commissions implementation analyst.

You have been given the following document content to classify.

Document filename: {filename}
Content preview (first 3000 characters): {content_preview}

Classify this document by returning a JSON object with these fields:
- source_type: one of [BRD, FDD, TDD, UserStory, ProcessDoc, MeetingNotes, Email, Chat, TestScript, DefectLog, IntegrationSpec, ConfigWorkbook, ReleaseNotes, SOP, Other]
- primary_component: one of [Workflow, BTP_EDL, ICM_Engine, Embedded_Analytics, Integration, Participants, Credit, Incentive, Batch, Security, Other]
- secondary_components: array of additional components covered
- estimated_author_role: one of [BusinessAnalyst, FunctionalConsultant, TechnicalArchitect, BusinessStakeholder, QALead, ProjectManager, Unknown]
- approximate_document_date: ISO date or null if unknown
- is_likely_stale: boolean — true if content appears older than 18 months or references superseded functionality
- classification_confidence: decimal 0.0 to 1.0
- classification_rationale: one sentence explaining classification decision

Return ONLY valid JSON. No preamble, no explanation outside the JSON object.
```

---

## Prompt 2: Requirement Candidate Extraction

```
You are a senior SAP Commissions business analyst and functional architect.

You are analyzing the following source material to extract atomic requirement candidates.

PROJECT CONTEXT: {project_context}
COMPONENT FOCUS: {component}
SOURCE MATERIAL:
---
{source_text}
---

Extract all requirement-relevant content from this material. For each candidate:

1. State the requirement precisely — not vaguely
2. Identify the candidate_type: RULE | ACTOR | TRIGGER | VALIDATION | EXCEPTION | DATA_FIELD | INTEGRATION | REPORTING | SECURITY | NON_FUNCTIONAL
3. Assign a confidence score 0.0 to 1.0 based on how clearly the requirement is stated in the source
4. Cite the exact source text segment that supports this candidate (verbatim quote, max 200 characters)
5. Flag if the statement is explicit (directly stated) or inferred (you derived it from context)
6. Flag if the statement conflicts with anything else in this material

Also identify:
- Any terms that need normalization (e.g. "agent" vs "participant", "deal" vs "transaction")
- Any acceptance conditions that are missing or untestable
- Any actors, system interfaces, or data fields mentioned but not defined
- Open questions this material raises but does not answer

Return a JSON object with:
{
  "candidates": [ { statement, candidate_type, confidence, source_quote, is_inferred, conflict_indicator } ],
  "terminology_flags": [ { term_used, recommended_term, rationale } ],
  "gaps": [ { description, gap_type } ],
  "open_questions": [ { question, why_it_matters } ]
}

Do not invent requirements. If source material is insufficient, say so explicitly in the gaps list.
```

---

## Prompt 3: Requirement Composition

```
You are a senior SAP Commissions functional consultant writing an enterprise-grade requirement.

You have been given a set of approved requirement candidates extracted from multiple source documents.

REQUIREMENT CANDIDATES:
{candidates_json}

CONFLICTS IDENTIFIED:
{conflicts_json}

OPEN QUESTIONS (unresolved):
{open_questions_json}

Produce a complete, structured requirement using the following schema. Every field must be explicitly populated. Do not use filler text. If a section cannot be completed from the available evidence, write "INSUFFICIENT INFORMATION: [reason]" rather than guessing.

REQUIREMENT SCHEMA:
- requirement_id_display: auto-assigned
- title: concise, action-oriented
- business_objective: what business outcome this enables (1-2 sentences, no fluff)
- in_scope: specific list of what this requirement covers
- out_of_scope: what is explicitly excluded
- background: context, history, why this exists
- actors: [ { role, description, system_or_human } ]
- preconditions: [ conditions that must be true before this process can execute ]
- trigger: what event or action initiates this process
- main_flow: [ { step_num, actor, action, system_response } ]
- alternate_flows: [ { condition, steps } ]
- exception_flows: [ { condition, handling, owner } ]
- business_rules: [ precise, testable rule statements ]
- data_requirements: [ { field, source_system, type, validation_rule } ]
- integration_touchpoints: [ { system, direction, method, data_exchanged, failure_handling } ]
- reporting_analytics_needs: description or null
- security_role_implications: description or null
- audit_reconciliation_implications: description or null
- non_functional_requirements: [ { type, description, measurable_target } ]
- assumptions: [ { text, basis, accepted } ]
- open_questions: [ { question, owner, blocking } ]
- acceptance_criteria: [ { id, text, testable: true/false } ]
- dependencies: [ description ]
- risks: [ { description, likelihood, impact, mitigation } ]

Return ONLY a valid JSON object matching this schema.

CRITICAL RULES:
- Every acceptance criterion must be testable. If it is not testable, set testable=false and flag it.
- Every assumption must be clearly marked as inferred, not stated as fact.
- Do not resolve open questions — list them as unresolved.
- Business rules must be precise enough that a developer could implement them without follow-up questions.
```

---

## Prompt 4: Conflict Detection

```
You are reviewing two requirement statements extracted from different source documents in an SAP Commissions implementation project.

SOURCE A:
- Document: {source_a_name} (date: {source_a_date}, type: {source_a_type})
- Statement: {statement_a}

SOURCE B:
- Document: {source_b_name} (date: {source_b_date}, type: {source_b_type})
- Statement: {statement_b}

Determine whether these statements are:
1. CONTRADICTORY — they cannot both be true
2. OVERLAPPING — they cover the same topic but are not necessarily contradictory
3. COMPLEMENTARY — they each add non-conflicting information about the same topic
4. UNRELATED — they appear similar but address different aspects

If CONTRADICTORY or OVERLAPPING:
- Explain the conflict clearly
- Rate severity: CRITICAL (blocks requirement), MAJOR (requires resolution before sign-off), MINOR (cosmetic or editorial)
- Recommend which source should take precedence and why (consider recency, document type, and sign-off authority)

Return JSON: { conflict_type, severity, explanation, recommended_precedence, precedence_rationale }
```

---

## Prompt 5: Test Case Generation

```
You are a senior QA lead and SAP Commissions domain expert.

You are generating test cases for the following approved requirement.

REQUIREMENT:
{requirement_json}

COMPONENT: {component}
REQUIREMENT ID: {req_id_display}

Generate comprehensive test coverage across these dimensions:
- POSITIVE: happy path, all conditions met
- NEGATIVE: invalid inputs, missing data, wrong actor, wrong state
- BOUNDARY: edge values for numeric fields, date boundaries, threshold conditions
- EXCEPTION: system failure, timeout, missing integration response, manual intervention required
- SECURITY: role boundary tests — access granted to correct role, denied to incorrect role
- INTEGRATION: upstream data not received, downstream system rejects payload, retry logic
- DATA_VALIDATION: field-level validation rules from business rules section
- WORKFLOW: state transition tests, escalation tests, SLA breach tests
- REGRESSION: tests that protect core business rules from future change

For each test case, produce:
{
  "scenario_id": "TS-{component}-{seq}",
  "case_id": "TC-{component}-{seq}-{case_num}",
  "title": concise title,
  "test_type": one of the types above,
  "objective": what this test verifies,
  "preconditions": [ list ],
  "test_data_requirements": description of data needed,
  "steps": [ { step_num, action, expected_result } ],
  "expected_result": overall pass condition,
  "postconditions": [ list ],
  "acceptance_criterion_id": the AC this test covers,
  "component": component name,
  "priority": CRITICAL | HIGH | MEDIUM | LOW,
  "notes": any SAP Commissions-specific setup notes
}

CRITICAL RULES:
- Every test case must link to a specific acceptance criterion from the requirement
- Do not generate generic tests — every step must reference actual field names, rule names, roles, and conditions from the requirement
- If an acceptance criterion has no test coverage, flag it explicitly
- Generate at minimum 2 positive, 2 negative, 1 boundary, 1 exception, and 1 security test case per requirement
- Tests must be executable by a real QA team without further interpretation
```

---

# SECTION 8 — SAMPLE REQUIREMENTS

---

## SAMPLE REQ 1 — WORKFLOW
### REQ-WF-001: Compensation Adjustment Approval Workflow

**Business Objective:**
Enable payroll managers and commission administrators to submit, review, and approve manual compensation adjustments in SAP Commissions with a documented, auditable approval chain, preventing unauthorized modifications to participant earnings.

**In Scope:**
- Single-level and two-level adjustment approval routing
- Adjustment submission form and workflow state management
- Approval, rejection, and return-for-correction flows
- Audit trail capture for all actions
- Email notification at each state transition

**Out of Scope:**
- Mass adjustment batch processing (covered in REQ-WF-007)
- Integration with GL for adjustment posting (covered in INT-001)
- UI for compensation statement display of approved adjustments

**Actors:**
| Role | Description |
|---|---|
| Commission Administrator | Initiates adjustment request |
| Line Manager | First-level approver for adjustments ≤ $5,000 |
| Payroll Manager | Second-level approver for adjustments > $5,000 or escalated items |
| System | SAP Commissions Workflow Engine |

**Preconditions:**
- Participant record exists and is active in SAP Commissions
- Period is not in CLOSED status
- Initiating user has Commission Administrator role
- Adjustment amount is within configurable threshold for the workflow tier

**Trigger:**
Commission Administrator submits a compensation adjustment request from the Adjustment Request screen.

**Main Flow:**
1. Administrator completes adjustment form: participant ID, period, adjustment type, amount, justification
2. System validates all required fields and participant status
3. System determines approval tier based on adjustment amount
4. System creates workflow task and routes to designated approver
5. Approver receives email notification with link to approval screen
6. Approver reviews adjustment details and justification
7. Approver approves, rejects, or returns for correction
8. System updates adjustment status and notifies initiator
9. On approval: adjustment posted to calculation engine for period
10. On rejection: adjustment remains in REJECTED status with reason captured
11. System logs all actions to audit trail

**Business Rules:**
- BR-001: Adjustments ≤ $5,000 require single-level approval (Line Manager)
- BR-002: Adjustments > $5,000 require two-level approval (Line Manager then Payroll Manager)
- BR-003: An administrator may not approve their own adjustment request
- BR-004: Approval task must be actioned within 72 business hours or auto-escalated
- BR-005: Rejected adjustments may be resubmitted once with updated justification; second rejection is final
- BR-006: Adjustments to a LOCKED period are blocked at submission
- BR-007: Audit log entry must capture actor, timestamp, previous state, new state, and comment for every state transition

**Acceptance Criteria:**
- AC-001: Given a valid adjustment ≤ $5,000, the system routes to Line Manager only. [Testable]
- AC-002: Given a valid adjustment > $5,000, the system routes first to Line Manager, then to Payroll Manager upon Line Manager approval. [Testable]
- AC-003: An administrator cannot approve an adjustment they created. [Testable]
- AC-004: An unapproved approval task triggers an escalation notification after 72 business hours. [Testable]
- AC-005: All state transitions are recorded in the audit trail with actor, timestamp, and comment. [Testable]
- AC-006: Adjustment submission is blocked if the target period status is LOCKED. [Testable]

---

## SAMPLE REQ 2 — BTP/EDL
### REQ-EDL-001: Inbound Sales Transaction File Ingestion via BTP/EDL

**Business Objective:**
Ingest daily sales transaction files from the CRM system into SAP Commissions via BTP/EDL, applying schema validation, transformation, and error handling to ensure only clean, conformant transaction data reaches the ICM calculation engine.

**In Scope:**
- File arrival detection and ingestion trigger
- Schema and business validation rules
- Transformation logic for field mapping
- Error queue management for rejected records
- Retry logic for transient failures
- Ingestion audit trail

**Out of Scope:**
- ICM crediting logic (covered in REQ-ICM-001)
- CRM-side file generation and SFTP configuration

**Actors:**
| Role | Description |
|---|---|
| CRM System | Generates and delivers transaction file via SFTP |
| BTP/EDL Pipeline | Ingests, validates, and transforms file |
| SAP Commissions ICM Engine | Receives clean transaction records |
| Integration Operations Team | Monitors error queue and approves reprocessing |

**Main Flow:**
1. CRM deposits transaction file to SFTP landing zone at 02:00 daily
2. EDL pipeline detects file via scheduled trigger
3. Pipeline validates file format: delimiter, encoding, record count header
4. Pipeline validates each record against schema (required fields, data types, value ranges)
5. Records passing validation are transformed per field mapping specification
6. Clean records are loaded into SAP Commissions transaction staging table
7. Failed records are written to error queue with error code and description
8. Pipeline publishes ingestion summary: total records, passed, failed, error codes
9. If failed records exceed 5% threshold, pipeline sends alert to Integration Operations Team

**Business Rules:**
- BR-001: Transaction date must fall within current or one prior open commission period
- BR-002: Participant ID must exist and be active in SAP Commissions master data
- BR-003: Product code must exist in the SAP Commissions product catalogue
- BR-004: Transaction amount must be numeric, greater than zero, and within configurable maximum threshold
- BR-005: Duplicate transaction IDs within a processing window are rejected with error code DUP-001
- BR-006: Records rejected due to master data mismatch are held in error queue for 24 hours before auto-escalation
- BR-007: Retry of failed records requires explicit release by Integration Operations Team

**Acceptance Criteria:**
- AC-001: A file with all valid records loads completely to staging with zero errors. [Testable]
- AC-002: A record with an invalid participant ID is rejected with error code MDM-001 and written to error queue. [Testable]
- AC-003: A duplicate transaction ID within the same processing window is rejected with error code DUP-001. [Testable]
- AC-004: When failed records exceed 5% of file total, an alert is sent to the Integration Operations Team. [Testable]
- AC-005: Error queue records are not automatically reprocessed without explicit release by Integration Operations Team. [Testable]
- AC-006: Ingestion audit log captures file name, arrival time, record counts, and all error codes. [Testable]

---

## SAMPLE REQ 3 — ICM ENGINE
### REQ-ICM-001: Retroactive Crediting Adjustment for Territory Reassignment

**Business Objective:**
When a participant is retroactively reassigned to a new territory, recalculate and redistribute credit for all transactions falling within the reassignment effective period, ensuring accurate commission calculations for both the outgoing and incoming participant.

**In Scope:**
- Retroactive credit withdrawal from outgoing participant
- Retroactive credit assignment to incoming participant
- Recalculation trigger for affected periods
- Compensation statement impact
- Audit trail of credit redistribution

**Out of Scope:**
- Territory definition and hierarchy management
- Quota adjustment as a result of reassignment (addressed separately)

**Business Rules:**
- BR-001: Retroactive credit adjustments are only permitted for periods that are OPEN or PENDING_CLOSE; LOCKED periods require a manual override with Payroll Manager approval
- BR-002: Credit redistribution follows the effective date of the territory reassignment — transactions on or after effective date go to incoming participant
- BR-003: Recalculation must be triggered within one business day of the retroactive reassignment being approved
- BR-004: Both the outgoing and incoming participant must receive a revised compensation statement notification
- BR-005: Original credit records are not deleted; reversal records are created to maintain auditability
- BR-006: If recalculation results in a negative balance for the outgoing participant, a recovery workflow is triggered per REQ-WF-005

**Acceptance Criteria:**
- AC-001: Transactions on or after the retroactive effective date are credited to the incoming participant after reassignment approval. [Testable]
- AC-002: Transactions before the effective date remain credited to the outgoing participant. [Testable]
- AC-003: Original credit records are preserved; reversal records are created with reference to originals. [Testable]
- AC-004: Recalculation job is triggered within one business day of reassignment approval. [Testable]
- AC-005: Both participants receive revised compensation statement notification. [Testable]
- AC-006: Retroactive adjustment to a LOCKED period is blocked without Payroll Manager override. [Testable]

---

## SAMPLE REQ 4 — EMBEDDED ANALYTICS
### REQ-ANA-001: Sales Performance Dashboard — Region Manager View

**Business Objective:**
Provide Region Managers with a real-time, role-filtered view of commission attainment, pipeline performance, and team ranking within their assigned hierarchy, enabling data-driven coaching and compensation forecast decisions.

**In Scope:**
- Attainment % by participant within region
- Revenue vs quota comparison
- Period-to-date trend line
- Top/bottom performer ranking
- Drill-through to participant detail

**Out of Scope:**
- Compensation statement detail (accessible via separate Payee view)
- Forecast modelling (Phase 2)

**Business Rules:**
- BR-001: Region Manager can only view data for participants in their direct hierarchy — no cross-region visibility
- BR-002: Dashboard data must reflect calculation results from the last completed calculation run; real-time mid-period estimates are not displayed unless explicitly toggled
- BR-003: Attainment % is calculated as (YTD Commissions Earned / Target Incentive) × 100
- BR-004: Ranking is by attainment %, descending; ties broken by absolute commission amount
- BR-005: Drill-through to participant detail is available; drill-through to individual transaction is not available from this dashboard

**Acceptance Criteria:**
- AC-001: A Region Manager sees only participants in their assigned hierarchy — no data from other regions is visible. [Testable]
- AC-002: Attainment % is calculated correctly per BR-003. [Testable]
- AC-003: Dashboard data matches the output of the last completed calculation run for the selected period. [Testable]
- AC-004: Ranking is ordered by attainment % descending, with tie-breaking per BR-004. [Testable]
- AC-005: Drill-through to participant detail is available and displays correct data. [Testable]
- AC-006: A user without Region Manager role cannot access this dashboard. [Testable]

---

## SAMPLE REQ 5 — INTEGRATIONS
### REQ-INT-001: HR System Participant Sync — New Hire and Termination Events

**Business Objective:**
Synchronise participant master data between the HR system and SAP Commissions for new hire onboarding and termination processing, ensuring participants are activated or deactivated in Commissions within one business day of the HR event.

**In Scope:**
- New hire participant creation in SAP Commissions
- Termination participant deactivation
- Position and hierarchy assignment from HR organisational data
- Error handling for incomplete or invalid HR records

**Out of Scope:**
- Role or compensation plan assignment (manual process post-creation)
- HR system configuration

**Business Rules:**
- BR-001: A participant record must be created in SAP Commissions within one business day of the HR effective hire date
- BR-002: A terminated participant must be deactivated in SAP Commissions no later than the HR termination effective date
- BR-003: If the HR record is missing required fields (employee ID, job grade, reporting manager), the record is rejected and an alert is sent to HR Operations
- BR-004: Deactivated participants retain all historical data and commission records; records are not deleted
- BR-005: If a position code in the HR record does not exist in SAP Commissions, the participant is created without position assignment and flagged for manual resolution

**Acceptance Criteria:**
- AC-001: A valid new hire record creates a participant in SAP Commissions with correct attributes within one business day. [Testable]
- AC-002: A termination event deactivates the participant on or before the effective termination date. [Testable]
- AC-003: An HR record missing required fields is rejected, not partially created, and an alert is sent to HR Operations. [Testable]
- AC-004: Deactivated participants retain all historical records and are queryable in audit reports. [Testable]
- AC-005: A participant created with an unknown position code is flagged for manual resolution. [Testable]

---

# SECTION 9 — SAMPLE TEST CASES

## REQ-WF-001: Compensation Adjustment Workflow

**TC-WF-001-01 | POSITIVE | Priority: CRITICAL**
Title: Adjustment ≤ $5,000 routes to Line Manager only
Preconditions: Active participant, open period, initiator has Commission Administrator role
Steps:
1. Log in as Commission Administrator
2. Navigate to Adjustment Request screen
3. Enter participant ID, period, adjustment type = MERIT, amount = $3,500, justification text
4. Submit adjustment
Expected Result: Workflow task created and assigned to Line Manager; Payroll Manager receives no task; initiator receives "Submitted" notification
AC Link: AC-001

**TC-WF-001-02 | POSITIVE | Priority: CRITICAL**
Title: Adjustment > $5,000 routes through two-level approval
Steps:
1. Submit adjustment for $7,200
2. Line Manager approves
Expected Result: Task appears in Payroll Manager queue after Line Manager approval; adjustment reaches APPROVED only after both approve
AC Link: AC-002

**TC-WF-001-03 | NEGATIVE | Priority: CRITICAL**
Title: Administrator cannot approve their own adjustment
Preconditions: Adjustment submitted by Administrator A
Steps:
1. Log in as Administrator A
2. Navigate to pending approval task for their own adjustment
Expected Result: Approve button is absent or disabled; attempt via API returns 403 FORBIDDEN
AC Link: AC-003

**TC-WF-001-04 | BOUNDARY | Priority: HIGH**
Title: Approval threshold boundary — adjustment of exactly $5,000
Steps:
1. Submit adjustment for exactly $5,000
Expected Result: Routes to Line Manager only (≤ $5,000 rule applies)
AC Link: AC-001

**TC-WF-001-05 | EXCEPTION | Priority: HIGH**
Title: Approval task not actioned within 72 business hours
Preconditions: Adjustment submitted, approval task assigned to Line Manager
Steps:
1. Advance system clock by 73 business hours without Line Manager action
Expected Result: Escalation notification sent to Payroll Manager; task appears in Payroll Manager queue with ESCALATED flag
AC Link: AC-004

**TC-WF-001-06 | NEGATIVE | Priority: CRITICAL**
Title: Adjustment to LOCKED period is blocked
Steps:
1. Submit adjustment targeting a period with status = LOCKED
Expected Result: Submission blocked at validation; error message "Period is locked — adjustment not permitted"
AC Link: AC-006

**TC-WF-001-07 | SECURITY | Priority: HIGH**
Title: User without Commission Administrator role cannot submit adjustment
Steps:
1. Log in as user with read-only role
2. Attempt to navigate to Adjustment Request screen
Expected Result: Screen is inaccessible; API POST to /adjustments returns 403
AC Link: AC-003 (role boundary)

---

## REQ-EDL-001: Inbound Transaction Ingestion

**TC-EDL-001-01 | POSITIVE | Priority: CRITICAL**
Title: Valid file loads completely with zero errors
Test Data: File with 500 valid records, all fields populated, all participant IDs exist
Expected Result: 500 records loaded to staging; ingestion summary shows 500 passed, 0 failed
AC Link: AC-001

**TC-EDL-001-02 | NEGATIVE | Priority: CRITICAL**
Title: Record with invalid participant ID is rejected with correct error code
Test Data: File with 1 record containing participant ID not in SAP Commissions master data
Expected Result: Record written to error queue with error code MDM-001; not loaded to staging
AC Link: AC-002

**TC-EDL-001-03 | NEGATIVE | Priority: HIGH**
Title: Duplicate transaction ID within same processing window is rejected
Test Data: File containing two records with identical transaction ID
Expected Result: Second record rejected with error code DUP-001; first record processed normally
AC Link: AC-003

**TC-EDL-001-04 | BOUNDARY | Priority: HIGH**
Title: File with exactly 5% failed records does not trigger alert
Test Data: 100-record file, 5 records invalid
Expected Result: 5 records to error queue, no alert sent to Integration Operations Team
AC Link: AC-004

**TC-EDL-001-05 | BOUNDARY | Priority: HIGH**
Title: File with 5.1% failed records triggers alert
Test Data: 100-record file, 6 records invalid (rounding: >5%)
Expected Result: Alert sent to Integration Operations Team
AC Link: AC-004

**TC-EDL-001-06 | SECURITY | Priority: HIGH**
Title: Error queue records cannot be reprocessed without explicit release
Steps:
1. Place 10 records in error queue
2. Attempt to trigger reprocessing via API without Integration Operations Team role
Expected Result: 403 FORBIDDEN; records remain in queue
AC Link: AC-005

---

# SECTION 10 — PHASED BUILD PLAN

## MVP (Weeks 1–8)

**Goal:** Prove the core extraction-to-approval loop for one component (Workflow).

Scope:
- Source intake: PDF, DOCX, TXT upload only
- Manual tagging of component (no auto-classification)
- Extraction for Workflow component only
- Requirement composition with full schema
- Human approval workflow (single reviewer)
- Test case generation for approved requirements
- Export to XLSX
- No traceability matrix yet
- No version diff viewer yet
- Single project, single team

Deliverables:
- `apps/api` with intake, extraction, requirements, approval, testgen modules
- `apps/web` with 5 core screens (Intake, Extraction Workspace, Draft Review, Approval Console, Test Output)
- PostgreSQL schema, all migrations
- Celery worker for async extraction
- Full prompt set for Workflow component
- Demo dataset: 3 source documents → 1 approved requirement → test cases

---

## Phase 2 (Weeks 9–16)

**Goal:** Full domain coverage, traceability, versioning, conflict detection.

Additions:
- Auto-classification of all source types
- Extraction for all 5 components (Workflow, BTP/EDL, ICM, Analytics, Integrations)
- Conflict detection engine
- Full traceability matrix
- Version diff viewer
- Multi-reviewer approval chain
- Requirement quality score with enforcement threshold
- Re-validation when new source conflicts with approved requirement
- Export to JSON and ALM format

---

## Enterprise Hardening (Weeks 17–24)

**Goal:** Production-ready for real enterprise delivery.

Additions:
- Auth0 / Entra ID SSO integration
- Full audit log with immutable storage
- Role-based access control (BA, Reviewer, QA Lead, Admin, Read-Only)
- Multi-project and multi-tenant support
- Batch import (ZIP of artifacts)
- Deduplication engine
- Semantic search across all source material
- Scheduled staleness alerts
- Kubernetes deployment manifests
- Monitoring and alerting (Prometheus + Grafana or Azure Monitor)
- Full test coverage for services
- API documentation

---

# SECTION 11 — KEY RISKS AND FAILURE MODES

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AI extracts plausible but incorrect requirements from ambiguous source material | HIGH | CRITICAL | Confidence scoring, source citation mandatory, human review gate, "INSUFFICIENT INFORMATION" fallback |
| Requirement approved before open questions are resolved | HIGH | HIGH | System flags unresolved blocking questions; approval can proceed but creates explicit warning in record |
| Test cases generated that are unmappable to real SAP Commissions configuration | MEDIUM | HIGH | Domain-specific prompts; test case review by functional consultant before export |
| Source material contains contradictory decisions across documents; AI picks one silently | HIGH | CRITICAL | Conflict detection runs before composition; conflicts must be resolved or accepted before composition proceeds |
| Performance degradation on large document sets (100+ files) | MEDIUM | HIGH | Chunking, async processing, vector search instead of full-text |
| Requirement versioning creates confusion about which version tests belong to | MEDIUM | HIGH | Tests always link to a specific RequirementVersion ID; deprecated tests flagged automatically |
| Users treat AI-generated requirements as final without review | HIGH | CRITICAL | UI language enforces "AI Draft — Not Approved"; approval flow cannot be bypassed via API |
| Sensitive business data (compensation amounts, personal data) sent to external AI API | HIGH | CRITICAL | PII stripping option before AI call; on-premise inference option in architecture; data consent flag per project |
| Tool adopted but not maintained — requirements drift from implemented system | MEDIUM | HIGH | Re-validation on new source import; staleness flags; version control enforced |

---

# SECTION 12 — RECOMMENDATIONS FOR ENTERPRISE GRADE

1. **Build a domain vocabulary file, not just prompts.**
Maintain a structured `sap_commissions_domain.json` that defines canonical terms, synonyms, and their relationships. All prompts inject this vocabulary. This prevents "agent vs participant vs payee" confusion degrading extraction quality over time.

2. **Treat the AI layer as replaceable infrastructure.**
The AI client is behind an interface. Swap Claude for Azure OpenAI or an on-premise model without touching business logic. This matters for data residency compliance.

3. **Source priority weighting is a business policy, not an AI decision.**
Build a configurable source priority matrix: signed-off FDDs outweigh meeting notes; recent chats can override stale docs if explicitly marked as scope decisions. Make this visible and editable by the project team.

4. **Enforce quality gates programmatically, not by convention.**
Requirement quality score must meet a configurable threshold before submission for approval is allowed. Acceptance criteria must all be marked testable=true before test generation runs. These are not suggestions — they are enforced in service layer code.

5. **Build for re-run, not for single pass.**
When a new source contradicts an approved requirement, the system must surface this automatically. The traceability model must support: source → snippet → candidate → requirement version → test case, with cascading invalidation flags when any node in the chain is updated.

6. **Make explainability a first-class feature.**
Every AI output must show its reasoning. A reviewer should never have to trust a requirement statement without being able to click through to the source evidence. This is what separates this tool from a word processor with AI bolted on.

7. **Design for the QA team, not just the analyst.**
Test cases must be executable without follow-up questions. Steps must name actual screens, fields, roles, and expected system messages. Generic steps like "verify the system behaves correctly" are rejected by the quality gate.

8. **Invest in the conflict resolution UX.**
Conflict detection is only valuable if the resolution workflow is usable. Side-by-side comparison of conflicting statements, with source metadata and recency indicators, is the highest-value UX investment after the approval flow.

9. **Audit log is non-negotiable from day one.**
Do not defer audit logging to Phase 2. Every mutation to a requirement, source classification, or test case must be logged immutably from the first production deployment. This is the tool's credibility with enterprise governance teams.

10. **Plan for the organizational change, not just the technology.**
The highest risk of failure is not technical — it is that analysts continue writing requirements in Word documents and test cases in Excel because the tool adds friction. The MVP must be demonstrably faster than the existing process for the two most common tasks: composing a requirement and generating a test set.

---

*Document version: 1.0 | Status: Architecture Proposal — Pending Checkpoint 2 Approval*
