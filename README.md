# Synthetic Census

A demographic simulation tool that queries diverse AI personas to analyze public sentiment on issues. Uses isolated API calls for each sample to ensure response independence.

## How It Works

```
┌─────────────────┐
│  GitHub Action  │
│    Trigger      │
└────────┬────────┘
         │
         ▼
┌───────────────────────────────────────┐
│         For Each Persona:             │
│  ┌─────────────────────────────────┐  │
│  │  Sample 1: Isolated API Call    │  │
│  │  Sample 2: Isolated API Call    │  │
│  │  Sample 3: Isolated API Call    │  │
│  └─────────────────────────────────┘  │
│         (No cross-contamination)      │
└───────────────────┬───────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │   Aggregation   │
           │   API Call      │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  Final Report   │
           │   Committed     │
           └─────────────────┘
```

## Quick Start

### 1. Add Your API Key

Go to: **Repository → Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

### 2. Run a Simulation

1. Go to **Actions** tab
2. Select **Run Synthetic Census**
3. Click **Run workflow**
4. Fill in the parameters:
   - `use_case_id`: `ai_job_impact` (or your own)
   - `question`: Your question
   - `samples_per_persona`: 3 (default)
   - `temperature`: 0.7 (default)
5. Wait for completion
6. Find results in `outputs/{use_case_id}/{run_id}/`

## Creating a New Use Case

1. Create folder: `personas/your_use_case_id/`
2. Add persona `.md` files (see examples in `personas/ai_job_impact/`)
3. Commit and push
4. Run simulation with your new `use_case_id`

## Persona File Format

Each `.md` file should include:

```markdown
You are a [age]-year-old [occupation] in [location]. [Key details about job, income, life situation].

Information sources: [Where they get information]

Priorities: [What matters to them]

Perspective on [topic]: [Their relevant viewpoint]

Communication style: [How they express themselves]

When answering questions, respond authentically as this person would—with their specific knowledge, concerns, and blind spots. Keep responses to 150-200 words.
```

## Output Structure

```
outputs/
├── {use_case_id}/
│   ├── run_20241229_143022/
│   │   ├── config.json       # Run configuration
│   │   ├── responses.json    # All raw responses
│   │   └── report.md         # Full analysis
│   ├── run_20241229_160145/
│   │   └── ...
│   └── latest.md             # Most recent report
```

## Configuration Options

| Input | Default | Description |
|-------|---------|-------------|
| `use_case_id` | (required) | Folder name under `personas/` |
| `question` | (required) | Question to ask all personas |
| `samples_per_persona` | 3 | Independent API calls per persona |
| `temperature` | 0.7 | Sampling randomness (0.0-1.0) |

## Why Isolated API Calls?

Each persona sample is a completely independent API call because:

1. **No context contamination**: Persona B doesn't "see" Persona A's response
2. **System prompt adherence**: Personas are passed as system prompts (stronger behavioral lock)
3. **True variance measurement**: If same persona gives different answers, it indicates genuine ambivalence
4. **Statistical independence**: Samples are truly independent for analysis

## API Usage

Each run makes this many API calls:

```
(Number of personas × Samples per persona) + 1 aggregation call
```

**Example:** 5 personas × 3 samples + 1 = **16 API calls**

## Example Questions

- `"How worried are you that AI will significantly impact your job in the next 5 years?"`
- `"Would you buy an electric vehicle as your next car?"`
- `"How do you feel about your children using AI tutors for homework?"`
- `"Should companies require employees to return to office full-time?"`

## Tips

- **5-8 personas** per use case gives good coverage without excessive API costs
- **3 samples** is usually sufficient; use 5 for higher-stakes analysis
- Make personas **authentic, not caricatures**—include nuance and internal conflict
- Vary **demographics that actually matter** for your specific question
- Include personas who might be **genuinely conflicted** on the issue
