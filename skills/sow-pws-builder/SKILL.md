---
name: sow-pws-builder
description: >
  Build Statements of Work (SOW) or Performance Work Statements (PWS) for
  federal contracts through a structured scope decision workflow that produces
  a contract-file-ready document with an implied staffing table. Use this skill
  whenever the user asks to write a SOW, PWS, statement of work, performance
  work statement, convert a SOO to a SOW/PWS, develop requirements, define
  contract scope, build a work statement, or draft requirement language. Also
  trigger when the user says they need a SOW/PWS before building an IGCE, when
  they have a SOO and need to develop it into executable requirements, or when
  they need to reduce scope to fit a budget and need to know what to cut.
  This skill produces the structured requirement document that feeds directly
  into the IGCE Builder skills (FFP, LH/T&M, CR) — it is the upstream input
  those skills need. Do NOT use for IGCEs themselves (use IGCE Builder skills).
  Do NOT use for market research reports (use Market Research Builder).
---

# SOW/PWS Builder

**Version 1.0** | March 2026

## Overview

This skill walks a program office (or analyst acting on their behalf) through structured scope decisions and assembles the answers into a properly formatted SOW or PWS. The core insight: the program office doesn't need to know FTE counts or cost estimates up front — they need to make scope decisions, and staffing falls out as a derived output.

**Output:** A .docx SOW or PWS with standard federal sections, plus a staffing implications table ready for handoff to any IGCE Builder skill.

**No external APIs required.** This is a decision tree + document generation skill.

**Regulatory basis:** FAR 37.602 (performance-based acquisition), FAR 46.401 (quality assurance), FAR 7.105 (written acquisition plans — requirement description).

## Workflow Selection

### Workflow A: Full Build (Default)
User needs a SOW/PWS from scratch or from a rough concept. Execute all three phases.
Triggers: "write a SOW," "build a PWS," "I need a work statement for..."

### Workflow B: SOO Conversion
User has an existing SOO and needs it developed into a SOW/PWS. Start with Phase 0 (SOO intake), then Phases 1–3.
Triggers: "convert this SOO to a SOW," "develop this SOO into a PWS," "we have a SOO and need a work statement."

### Workflow C: Scope Reduction
User has an existing SOW/PWS or IGCE output that exceeds budget. Walk through scope decision tree to identify what to cut, then produce a revised document.
Triggers: "this is too expensive, what can we cut," "reduce scope to fit budget," "need to descope."

## Document Type Selection

Ask at the start: **SOW or PWS?**

| | SOW | PWS |
|---|---|---|
| Prescribes | Tasks and methods (how) | Outcomes and standards (what) |
| Contractor flexibility | Low — government directs approach | High — contractor proposes approach |
| Best for | Well-understood, repeatable work | Complex or innovative requirements |
| QASP focus | Task completion | Performance metrics |
| FAR preference | — | FAR 37.602 prefers PBA/PWS |

If the user is unsure, default to PWS — it's the FAR-preferred approach for services and gives the contractor room to propose efficient solutions. The decision tree is identical either way; only the output language changes.

## Phase 0: SOO Intake (Workflow B Only)

When the user provides an existing SOO:

1. **Read and extract.** Parse the SOO for: background, objectives, constraints, performance location, period of performance, known systems, volume data, key personnel, security requirements, and any appendix data.

2. **Gap identification.** Flag what the SOO provides vs. what a SOW/PWS needs:
   - ✅ Typically present in SOO: background, high-level objectives, constraints, PoP, location
   - ❌ Typically missing from SOO: task decomposition, staffing, deliverables with acceptance criteria, CLIN structure, QASP metrics, reporting cadence, transition details

3. **Decision bridge.** Present the gaps as the questions Phase 1 will answer. Frame it as: "The SOO tells us what the agency wants to achieve. Phase 1 asks the questions that turn objectives into executable requirements."

4. **Carry forward.** Pre-populate Phase 1 answers with anything the SOO already decided (location, PoP, known constraints). Don't re-ask settled questions.

## Phase 1: Scope Decision Tree

Ask questions in this sequence. Each decision narrows scope and implies staffing. Present as structured choices, not open-ended questions. Collect in a single pass where possible.

### Block 1: Mission and Service Model

1. **What is the core service?** (Provide options based on context, or ask open-ended if starting from scratch)
2. **Service delivery model:** Government FTEs with contractor augmentation | Fully contracted service | Hybrid (specify which functions are FTE vs. contractor)
3. **Coverage model:** Business hours (M-F 8-5) | Extended hours (specify) | 24/7/365 | Seasonal/surge
4. **Geographic scope:** Single site | Multi-site (how many?) | Virtual/remote | Hybrid

### Block 2: Technical Scope

5. **Build vs. Buy:** Custom development | COTS/SaaS configuration | Hybrid (custom integrations on COTS platform)
6. **Systems in scope:** List all systems the contractor will build, configure, integrate with, or maintain. For each: new build vs. existing system.
7. **Integration complexity:** Standalone | Integrates with 1-3 systems | Integrates with 4+ systems | Enterprise-wide integration
8. **Data migration:** No legacy data | Migrate from 1-2 sources | Migrate from 3+ sources | Complex multi-system consolidation
9. **AI/automation:** None | Basic automation (IVR, rules-based routing) | AI-assisted (NLP, ML classification) | Advanced AI (chatbots, predictive analytics)

### Block 3: Scale and Volume

10. **Transaction/contact volume:** Provide numbers if known, or characterize as low/medium/high
11. **User population:** Internal users (how many?) | External/public-facing | Both
12. **Concurrent user requirements:** If applicable
13. **Growth expectations:** Stable | Moderate growth (10-25%/yr) | High growth (>25%/yr) | Unknown

### Block 4: Organizational Scope

14. **How many organizational units?** (offices, centers, divisions served)
15. **Phasing:** All at once | Phased rollout (how many phases?) | Pilot then expand
16. **Stakeholder complexity:** Single program office | Multiple offices, single agency | Cross-agency

### Block 5: Contract Structure

17. **Period of performance:** Base year + option years (how many?)
18. **Base year scope:** Full performance from day 1 | Ramp-up/transition-in period (how long?) | Design/development only, production in options
19. **CLIN structure preference:** By period (CLINs = base year, OY1, OY2...) | By function (CLINs = development, operations, maintenance, training) | By deliverable | Unsure (skill will recommend)
20. **Contract type:** FFP | T&M | LH | CR | Hybrid (specify)
21. **Transition requirements:** Transition-in from incumbent? | Transition-out plan required? | Both

### Block 6: Quality and Oversight

22. **Acceptable quality level (AQL):** For key performance metrics — e.g., 95% first-call resolution, 99.95% uptime, <2hr mean time to resolve
23. **Reporting cadence:** Weekly | Monthly | Quarterly | As-needed
24. **Key personnel:** Which roles must be designated as key? (PM always; others?)

### Decision-to-Staffing Derivation Rules

After collecting decisions, derive the staffing implications. These are heuristics, not formulas:

| Decision | Staffing Implication |
|---|---|
| 24/7 coverage | Minimum 3x the single-shift headcount for covered roles |
| Custom development | 1 architect + 2-4 developers per major system/module |
| COTS configuration | 1 architect + 1-2 configurators per platform |
| AI/NLP components | +1-2 data scientists or ML engineers |
| 4+ system integrations | +1-2 integration/middleware engineers |
| Data migration from 3+ sources | +1 data engineer + 1 DBA (may be time-limited to base year) |
| Multi-site or 3+ org units | +1 change management/training specialist per 2-3 units |
| Contact center: volume ÷ 250 days ÷ contacts/agent/day | = required agent headcount (adjust for FTE vs. contractor split) |
| Agile development | 1 scrum master or PM per 2 dev teams (team = 5-7 people) |
| FISMA/security requirements | +1 information security analyst |
| O&M phase | Typically 40-60% of development-phase staffing |
| Transition-in | +0.5-1 FTE for knowledge transfer (time-limited) |

**Present the derived staffing table to the user for validation before proceeding to Phase 2.** Format:

```
Task Area               | Labor Category      | Est. FTEs | Derivation Basis        | Phase
Development             | Solution Architect  | 1         | Enterprise CRM platform | Base-OY1
Development             | Software Developer  | 4         | 2 Agile teams × 2 devs  | Base-OY1
Operations              | Tier 1 Agent        | 10        | 127K contacts ÷ vol/day | Base-OY4
O&M                     | Systems Admin       | 2         | 50% of dev staffing     | OY2-OY4
```

**User validation gate.** The user confirms, adjusts, or overrides any line. If they override, document the override reason — it matters for the IGCE methodology narrative.

## Phase 2: Document Assembly

Generate the SOW or PWS using the docx skill. Read `/mnt/skills/public/docx/SKILL.md` before generating output.

### SOW/PWS Section Structure

**Section 1: Introduction**
- 1.1 Purpose
- 1.2 Background (from SOO or user input)
- 1.3 Scope Summary (one paragraph synthesizing all Phase 1 decisions)
- 1.4 Applicable Documents and Standards

**Section 2: Definitions and Acronyms**

**Section 3: Requirements** (this is the core — structure depends on SOW vs. PWS)

*For SOW:* Section 3 is organized by task area. Each task has:
- Task number and title
- Task description (what the contractor shall do)
- Subtasks if applicable
- Deliverables produced by this task
- Government-furnished resources for this task

*For PWS:* Section 3 is organized by performance objective. Each objective has:
- Objective number and title
- Required outcome (what the contractor shall achieve)
- Performance standard (measurable threshold)
- Acceptable Quality Level
- Method of assessment (inspection, demonstration, analysis, test)
- Incentive/disincentive if applicable

**Section 4: Deliverables**
- Deliverables table: ID | Title | Description | Format | Frequency | Due Date/Trigger | Acceptance Criteria
- Standard deliverables to always include: Monthly Status Report, Transition-In Plan (if applicable), Transition-Out Plan, System Documentation, Training Materials

**Section 5: CLIN Structure**
- Map deliverables and tasks/objectives to CLINs
- Note which CLINs are priced (FFP) vs. estimated (T&M/LH) vs. cost-reimbursable
- Include CLIN descriptions suitable for the schedule

**Section 6: Period of Performance**

**Section 7: Place of Performance**

**Section 8: Government-Furnished Property/Information**

**Section 9: Security Requirements**

**Section 10: Key Personnel**
- Roles, minimum qualifications, certification requirements
- Only roles where government needs approval of specific individuals

**Section 11: Reporting and Oversight**
- Reporting schedule and content requirements
- Meeting cadence (kickoff, weekly status, monthly program review, quarterly executive)
- Points of contact

**Section 12: Quality Assurance Surveillance Plan (QASP) Summary**
- Performance metrics table: Metric | Standard | AQL | Method | Frequency | Incentive
- Full QASP may be a separate document; include summary here

**Section 13: Transition**
- 13.1 Transition-In (if applicable): knowledge transfer, incumbent cooperation, parallel operations
- 13.2 Transition-Out: data return, documentation, contractor cooperation, timeline

**Section 14: Constraints and Assumptions**

**Appendices** (as applicable):
- A: Current Environment Description
- B: Volume Data and Historical Metrics
- C: System Interface Specifications
- D: Acronym List

### Language Rules

**SOW language:** "The contractor shall [verb]..." — prescriptive, task-oriented.
**PWS language:** "The contractor shall achieve/maintain/ensure..." — outcome-oriented, measurable.

**Avoid:**
- "Support" as a standalone verb (too vague — support how?)
- "As needed" or "as required" without defining the trigger
- "Best practices" without specifying which standard
- "Coordinate with" without specifying the deliverable or decision that results
- Requirements that cannot be measured or verified

**Every requirement must be:** specific, measurable, achievable, relevant, and time-bound. If a requirement fails any of these, flag it for the user during assembly.

## Phase 3: Validation and Handoff

### Document Review Checklist

Before presenting the final document, verify:

- [ ] Every task/objective maps to at least one deliverable
- [ ] Every deliverable maps to at least one CLIN
- [ ] Every CLIN has a pricing basis (FFP, T&M, etc.)
- [ ] Key personnel roles match the staffing table
- [ ] Security requirements are consistent throughout
- [ ] Period of performance matches CLIN structure
- [ ] QASP metrics are measurable and have defined AQLs
- [ ] Transition-in/out timelines are realistic
- [ ] No orphaned requirements (stated but never deliverable-mapped)
- [ ] No scope gaps (Phase 1 decisions not reflected in requirements)

### Staffing Handoff Table

Produce a clean staffing table formatted for IGCE Builder consumption:

```
Labor Category          | SOC Code | FTEs | Phase        | Hours/Yr | Notes
Project Manager         | 13-1082  | 1    | Base-OY4     | 1,880    | Key personnel
Software Developer      | 15-1252  | 4    | Base-OY1     | 1,880    | Reduces to 1 in OY2+
Tier 1 Agent            | 43-4051  | 10   | Base-OY4     | 1,880    | Override: user set at 10
Systems Admin           | 15-1244  | 2    | OY2-OY4      | 1,880    | O&M phase only
```

Include columns for: labor category, SOC code, FTE count, active phases, productive hours, and notes (especially user overrides and derivation basis).

**Tell the user:** "This staffing table is ready for the IGCE Builder. Copy this conversation's output or say 'build the IGCE' and I'll hand it off to the FFP/T&M/CR skill based on your contract type selection."

## Edge Cases

**User doesn't know the answer to a decision:** Provide a recommended default with rationale. Mark it as an assumption in the document. Example: "If you're unsure about coverage model, business hours (M-F 8-5) is the default for non-emergency federal contact centers. I'll mark this as an assumption you can revisit."

**SOO is too vague to decompose:** If the SOO is under 300 words or provides fewer than 3 actionable scope details, tell the user: "This SOO doesn't have enough specificity to convert directly. I'll use it as background context, but Phase 1 will need to collect most decisions fresh."

**Scope exceeds single contract:** If Phase 1 decisions imply >50 FTEs, >$75M, or span >3 distinct technical domains, flag that this may need to be broken into multiple contracts. Suggest logical break points (e.g., development vs. operations, platform vs. contact center staffing).

**User wants to skip Phase 1:** Don't let them. The decision tree is the value. If they say "just write the SOW from this SOO," explain: "The SOO describes objectives, but a SOW requires decisions the SOO intentionally leaves open — like staffing model, build vs. buy, phasing, and CLIN structure. These take about 10 minutes to walk through, and they're what make the SOW defensible."

**Budget-constrained scope reduction (Workflow C):** When reducing scope to fit budget, work backwards: identify the highest-cost labor categories from the IGCE, map them to tasks/objectives, and present trade-offs: "Removing 24/7 coverage saves ~$X by eliminating night-shift agents, but means no live response outside business hours. Replacing custom AI with COTS chatbot saves ~$Y in developer FTEs but limits NLP accuracy." Let the user choose which scope reductions are acceptable, then regenerate affected SOW/PWS sections.

## What This Skill Does NOT Cover

- **Pricing or cost estimates** — use IGCE Builder skills (FFP, LH/T&M, CR)
- **Market research** — use Market Research Builder
- **Source selection criteria** — separate document, though CLIN structure informs it
- **J&A or sole source justification** — separate document
- **Full QASP** — this skill includes a QASP summary table; a detailed QASP with surveillance schedules is a separate deliverable
- **Clause selection (Section I/L)** — requires contracting officer determination per FAR Parts 12, 15, 16, 52
- **Contract type determination** — this skill accepts the user's contract type decision; it does not advise on which type to select (that's a FAR 16 analysis)
