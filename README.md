# SwarmLens

**SwarmLens** is an open-source investigation toolkit for detecting coordinated inauthentic behavior in public social media datasets.

It is built for researchers, trust & safety teams, policy analysts, journalists, investigators, and digital risk teams who need to understand whether a campaign looks organic, automated, or strategically amplified.

SwarmLens does **not** scrape private data, bypass access controls, or claim certainty. It analyzes datasets that were collected lawfully from public sources and produces **probabilistic, explainable indicators** for human review.

---

## Why SwarmLens exists

Most low-quality tools stop at a single question:

> "Is this account a bot?"

Real influence operations are more complicated.

A campaign can combine:
- low-quality bot accounts
- manually operated burner accounts
- copied talking points
- synchronized posting windows
- circular engagement rings
- coordinated amplification against a target account or hashtag

SwarmLens focuses on the **network**, the **timing**, and the **message reuse** — not just a single profile score.

---

## What SwarmLens analyzes

### Account-level risk scoring
Each account receives:
- bot probability score
- risk grade
- reasons and supporting evidence
- activity and trust metrics

### Coordination detection
SwarmLens looks for:
- exact phrase reuse across accounts
- near-duplicate messages
- synchronized posting bursts
- repeated interactions between the same accounts
- suspicious cluster formation

### Authenticity analysis
SwarmLens estimates:
- engagement authenticity around target accounts
- suspicious support ratio
- concentration of amplifying actors

### Network analysis
SwarmLens builds:
- suspicious pair links
- high-centrality account lists
- cluster summaries
- an interactive graph in the HTML dashboard

### Reporting
SwarmLens outputs:
- clean JSON report
- interactive HTML report
- explainable per-account evidence

---

## Core features

- Fast folder-based workflow
- Simple commands
- Works on CSV or JSON datasets
- Interactive local dashboard
- Explain-account mode
- Demo dataset included
- No external platform dependencies
- Clean GitHub-ready structure

---

## Quick start

### 1) Install

```bash
python -m venv .venv
.venv\Scriptsctivate
pip install -e .
```

### 2) Create a demo case

```bash
swarmlens init-case demo-case
```

### 3) Run a full scan

```bash
swarmlens run demo-case --clean -o report
```

### 4) Open the interactive dashboard

```bash
swarmlens dashboard report
```

### 5) Explain a specific account

```bash
swarmlens explain a004 -r report/report.json
```

---

## Command reference

### Run analysis
```bash
swarmlens run <case-folder>
swarmlens scan <case-folder>
```

### Validate input files
```bash
swarmlens validate <case-folder>
```

### Investigate one account
```bash
swarmlens explain <account-id> -r report/report.json
```

### Open dashboard
```bash
swarmlens dashboard <report-folder>
```

### Bootstrap a sample case
```bash
swarmlens init-case <output-folder>
```

---

## Expected case structure

A case folder can contain CSV or JSON files:

```text
case-folder/
├── accounts.csv
├── posts.csv
└── interactions.csv
```

### `accounts.csv`
Supported fields:
- `account_id`
- `username`
- `created_at`
- `followers_count`
- `following_count`
- `posts_count`
- `bio`
- `profile_image_default`
- `verified`
- `platform`

### `posts.csv`
Supported fields:
- `post_id`
- `account_id`
- `timestamp`
- `text`
- `hashtags`
- `replies_count`
- `likes_count`
- `shares_count`
- `target_account_id`

### `interactions.csv`
Supported fields:
- `source_account_id`
- `target_account_id`
- `interaction_type`
- `timestamp`

---

## What the report gives you

SwarmLens generates a report package with:

- `report.json` — full machine-readable findings
- `report.html` — interactive investigation dashboard

The HTML dashboard includes:
- account risk ranking
- searchable evidence tables
- campaign timeline visualization
- repeated-message evidence
- cluster summaries
- suspicious pairs table
- engagement authenticity table
- network graph overview

---

## Example workflow

```bash
swarmlens init-case my-case
swarmlens validate my-case
swarmlens run my-case --clean -o my-report
swarmlens dashboard my-report
swarmlens explain a004 -r my-report/report.json
```

---

## Reliability and trust model

SwarmLens is intentionally opinionated in one way:

It does **not** pretend to prove intent.

It produces structured indicators so an analyst can prioritize manual review.
A high score does **not** prove that an account is controlled by a bot operator, belongs to a state actor, or violates any specific platform rule.

This design makes the output more honest, more useful, and easier to defend in real investigations.

---

## Roadmap

Planned next-stage additions:
- multi-platform schema adapters
- case metadata and analyst notes
- richer graph layouts
- exportable case briefs
- rule packs for campaign archetypes
- optional streaming ingestion adapters

---

## GitHub presentation checklist

To make the repository look strong on GitHub:

- add screenshots from `report.html`
- keep one sample case in `swarmlens/demo_data/`
- pin the repository on your profile
- add repository topics such as:
  - `bot-detection`
  - `osint`
  - `social-media-analysis`
  - `network-analysis`
  - `cybersecurity`
  - `trust-and-safety`
  - `information-operations`

Recommended repository description:

> Advanced toolkit for detecting coordinated inauthentic behavior, suspicious bot swarms, and manipulated engagement in public social media datasets.

---

## License

MIT License
