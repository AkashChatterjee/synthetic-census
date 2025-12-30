#!/usr/bin/env python3
"""
Synthetic Census Simulation Runner

Makes isolated API calls for each persona sample to avoid context contamination.
Each persona is queried N times independently, then results are aggregated.
"""

import anthropic
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def query_persona(
    client: anthropic.Anthropic,
    system_prompt: str,
    question: str,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 500,
    temperature: float = 0.7
) -> str:
    """
    Make a single isolated API call for one persona sample.

    Each call is completely independent - no shared context.
    """
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text


def aggregate_responses(
    client: anthropic.Anthropic,
    cohort_id: str,
    question: str,
    all_responses: dict,
    model: str = "claude-sonnet-4-5-20250929",
    custom_aggregation_prompt: Optional[str] = None
) -> str:
    """
    Make a single API call to aggregate and analyze all responses.

    Args:
        client: Anthropic API client
        cohort_id: Identifier for the cohort
        question: The question asked to personas
        all_responses: Dictionary of all persona responses
        model: Model to use for aggregation
        custom_aggregation_prompt: Optional custom prompt to guide aggregation.
                                   If None, uses the default comprehensive analysis format.
    """

    # Build clean response summary for analysis
    responses_for_analysis = {}
    for persona_id, data in all_responses.items():
        responses_for_analysis[data["label"]] = data["samples"]

    total_samples = sum(len(data["samples"]) for data in all_responses.values())

    # Use custom prompt if provided, otherwise use default
    if custom_aggregation_prompt:
        # Include context in custom prompt
        aggregation_prompt = f"""You are a senior research analyst synthesizing results from a demographically diverse panel study.

STUDY CONFIGURATION
- Cohort: {cohort_id.replace("_", " ").title()}
- Personas Surveyed: {len(all_responses)}
- Samples Per Persona: {len(next(iter(all_responses.values()))["samples"])}
- Total Independent Responses: {total_samples}
- Methodology: Each response was generated via isolated API call (no cross-contamination)

QUESTION ASKED
{question}

RESPONSES BY PERSONA
Each persona was queried multiple times independently. Variance across samples indicates ambivalence; consistency indicates conviction.

{json.dumps(responses_for_analysis, indent=2)}

---

{custom_aggregation_prompt}
"""
    else:
        aggregation_prompt = f"""You are a senior research analyst synthesizing results from a demographically diverse panel study.

STUDY CONFIGURATION
- Cohort: {cohort_id.replace("_", " ").title()}
- Personas Surveyed: {len(all_responses)}
- Samples Per Persona: {len(next(iter(all_responses.values()))["samples"])}
- Total Independent Responses: {total_samples}
- Methodology: Each response was generated via isolated API call (no cross-contamination)

QUESTION ASKED
{question}

RESPONSES BY PERSONA
Each persona was queried multiple times independently. Variance across samples indicates ambivalence; consistency indicates conviction.

{json.dumps(responses_for_analysis, indent=2)}

---

Provide a comprehensive analysis with these sections:

## Executive Summary
3-4 sentences capturing the key findings and overall sentiment distribution.

## Intra-Persona Consistency Analysis

For each persona, analyze their response consistency across samples:

| Persona | Consistency | Interpretation |
|---------|-------------|----------------|
| [Name]  | High/Medium/Low | [What this suggests about their conviction] |

Note any personas whose views shifted notably across samples—this suggests genuine ambivalence or complexity on the issue.

## Cross-Persona Analysis

### Points of Consensus
What do most or all personas agree on? How strong is this agreement?

### Key Fault Lines
Where do opinions diverge? Identify distinct "camps" and which personas fall into each.

### Unexpected Findings
Any surprising alignments or disagreements that challenge assumptions?

## Predicted Population Sentiment

Based on this panel, estimate how a broader population might break down:

| Position | Estimated % | Key Demographics |
|----------|-------------|------------------|
| [Position] | [Range]% | [Who holds this view] |

Note: These are directional estimates based on simulated perspectives, not actual polling data.

## Confidence Assessment

- **Confidence Level**: [Low/Medium/High]
- **Limiting Factors**: What perspectives might be missing?
- **Recommendations**: What additional personas would strengthen the analysis?

## Synthesized Article

Write a 500-word article summarizing public sentiment on this issue, written as a journalist would. Include:
- The overall landscape of opinion
- Key points of tension and agreement
- Representative perspectives from different demographics (paraphrased, not quoted)
- Nuance and complexity rather than false balance
"""

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0.3,  # Lower temperature for analytical consistency
        messages=[{"role": "user", "content": aggregation_prompt}]
    )

    return response.content[0].text


def run_simulation(
    cohort_id: str,
    question: str,
    samples_per_persona: int = 3,
    temperature: float = 0.7,
    aggregation_prompt: Optional[str] = None
) -> None:
    """
    Run full simulation with isolated API calls per persona sample.

    Args:
        cohort_id: Identifier for the cohort (folder name under personas/)
        question: The question to ask all personas
        samples_per_persona: Number of independent samples per persona
        temperature: Sampling temperature (0.0-1.0)
        aggregation_prompt: Optional custom prompt to guide aggregation.
                           If None, uses default comprehensive analysis format.
    """

    # Initialize client
    client = anthropic.Anthropic()

    # Generate run_id
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Set up paths
    personas_dir = Path("personas") / cohort_id
    outputs_dir = Path("outputs") / cohort_id / run_id
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Validate personas directory
    if not personas_dir.exists():
        print(f"ERROR: Personas directory not found: {personas_dir}")
        print("Please create the directory and add persona .md files.")
        sys.exit(1)

    # Get persona files
    persona_files = sorted([
        f for f in personas_dir.glob("*.md")
        if f.name != ".gitkeep"
    ])

    if not persona_files:
        print(f"ERROR: No persona .md files found in {personas_dir}")
        sys.exit(1)

    total_api_calls = (len(persona_files) * samples_per_persona) + 1  # +1 for aggregation

    print(f"\n{'='*70}")
    print(f"SYNTHETIC CENSUS SIMULATION")
    print(f"{'='*70}")
    print(f"Cohort ID       : {cohort_id}")
    print(f"Run ID          : {run_id}")
    print(f"Question        : {question}")
    print(f"Personas        : {len(persona_files)}")
    print(f"Samples/Persona : {samples_per_persona}")
    print(f"Temperature     : {temperature}")
    print(f"Total API Calls : {total_api_calls}")
    print(f"{'='*70}\n")

    # Save config
    config = {
        "cohort_id": cohort_id,
        "run_id": run_id,
        "question": question,
        "samples_per_persona": samples_per_persona,
        "temperature": temperature,
        "aggregation_prompt": aggregation_prompt,
        "personas": [f.stem for f in persona_files],
        "total_api_calls": total_api_calls,
        "timestamp": datetime.now().isoformat(),
        "model": "claude-sonnet-4-5-20250929"
    }

    config_file = outputs_dir / "config.json"
    config_file.write_text(json.dumps(config, indent=2))
    print(f"Config saved to {config_file}\n")

    # Phase 1: Query each persona with isolated API calls
    print("PHASE 1: Querying Personas (Isolated API Calls)")
    print("-" * 50)

    all_responses = {}
    call_count = 0

    for persona_file in persona_files:
        persona_id = persona_file.stem
        persona_label = persona_id.replace("_", " ").title()
        system_prompt = persona_file.read_text().strip()

        print(f"\n  [{persona_label}]")

        all_responses[persona_id] = {
            "label": persona_label,
            "persona_file": str(persona_file),
            "samples": []
        }

        for sample_num in range(1, samples_per_persona + 1):
            call_count += 1
            print(f"    Sample {sample_num}/{samples_per_persona} (API call {call_count}/{total_api_calls})...", end=" ", flush=True)

            try:
                response = query_persona(
                    client=client,
                    system_prompt=system_prompt,
                    question=question,
                    temperature=temperature
                )
                all_responses[persona_id]["samples"].append(response)
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")
                all_responses[persona_id]["samples"].append(f"[ERROR: {str(e)}]")

    # Save raw responses
    responses_file = outputs_dir / "responses.json"
    responses_file.write_text(json.dumps(all_responses, indent=2))
    print(f"\nRaw responses saved to {responses_file}")

    # Phase 2: Aggregate with single API call
    print(f"\n{'='*50}")
    print("PHASE 2: Aggregating Responses")
    print("-" * 50)
    print(f"Making aggregation API call ({total_api_calls}/{total_api_calls})...", end=" ", flush=True)

    try:
        analysis = aggregate_responses(
            client=client,
            cohort_id=cohort_id,
            question=question,
            all_responses=all_responses,
            custom_aggregation_prompt=aggregation_prompt
        )
        print("✓")
    except Exception as e:
        print(f"✗ Error: {e}")
        analysis = f"[AGGREGATION ERROR: {str(e)}]"

    # Compile full report
    full_report = f"""# Synthetic Census Report

## Metadata

| Field | Value |
|-------|-------|
| **Cohort** | `{cohort_id}` |
| **Run ID** | `{run_id}` |
| **Timestamp** | {datetime.now().strftime("%Y-%m-%d %H:%M UTC")} |
| **Personas** | {len(persona_files)} |
| **Samples/Persona** | {samples_per_persona} |
| **Total Responses** | {len(persona_files) * samples_per_persona} |
| **Temperature** | {temperature} |
| **Model** | claude-sonnet-4-5-20250929 |

## Question

> {question}

---

{analysis}

---

# Appendix A: Persona Definitions

"""

    for persona_file in persona_files:
        persona_id = persona_file.stem
        persona_label = persona_id.replace("_", " ").title()
        system_prompt = persona_file.read_text().strip()

        full_report += f"""## {persona_label}

**File:** `{persona_file}`
```

{system_prompt}

```
---

"""

    full_report += """# Appendix B: Raw Responses

Each persona was queried independently via isolated API calls. Responses are presented in order of collection.

"""

    for persona_id, data in all_responses.items():
        full_report += f"## {data['label']}\n\n"
        for i, sample in enumerate(data["samples"], 1):
            full_report += f"### Sample {i}\n\n{sample}\n\n"
        full_report += "---\n\n"

    # Save report
    report_file = outputs_dir / "report.md"
    report_file.write_text(full_report)

    # Save latest pointer
    latest_file = outputs_dir.parent / "latest.md"
    latest_file.write_text(full_report)

    # Print summary
    print(f"\n{'='*70}")
    print("SIMULATION COMPLETE")
    print(f"{'='*70}")
    print(f"Cohort          : {cohort_id}")
    print(f"Run ID          : {run_id}")
    print(f"Report          : {report_file}")
    print(f"Latest          : {latest_file}")
    print(f"API Calls Made  : {total_api_calls}")
    print(f"{'='*70}\n")


def main():
    """Parse arguments and run simulation."""

    if len(sys.argv) < 3:
        print("""
Synthetic Census - Demographic Perspective Simulator

Usage:
    python run_simulation.py <cohort_id> "<question>" [samples_per_persona] [temperature] [aggregation_prompt]

Arguments:
    cohort_id           Folder name under personas/ containing .md files
    question            The question to ask all personas (quote if contains spaces)
    samples_per_persona Number of independent samples per persona (default: 3)
    temperature         Sampling temperature 0.0-1.0 (default: 0.7)
    aggregation_prompt  Optional custom prompt to guide aggregation (quote if contains spaces)
                        If not provided, uses default comprehensive analysis format

Examples:
    python run_simulation.py tier_1_city "What are your thoughts on urban infrastructure?" 3 0.7
    python run_simulation.py ev_adoption "Would you buy an electric vehicle?" 5 0.8
    python run_simulation.py tier_1_city "What messaging would resonate?" 3 0.7 "Summarize as bullet points"

Output:
    outputs/{cohort_id}/run_{timestamp}/
        ├── config.json       # Run configuration
        ├── responses.json    # All raw responses
        └── report.md         # Full analysis report
    outputs/{cohort_id}/latest.md  # Pointer to most recent run
""")
        sys.exit(1)

    cohort_id = sys.argv[1]
    question = sys.argv[2]
    samples_per_persona = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    temperature = float(sys.argv[4]) if len(sys.argv) > 4 else 0.7
    aggregation_prompt = sys.argv[5] if len(sys.argv) > 5 else None

    run_simulation(
        cohort_id=cohort_id,
        question=question,
        samples_per_persona=samples_per_persona,
        temperature=temperature,
        aggregation_prompt=aggregation_prompt
    )


if __name__ == "__main__":
    main()
