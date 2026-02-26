# CI/CD Pipeline

## Workflow Overview

```mermaid
flowchart TD
    trigger["🔄 Push to master / PR to master"]

    subgraph quality["Quality Gates"]
        lint["Code Quality Checks<br/>(flake8, JSON validation)"]
        unit["Python Unit Tests<br/>(3.10, 3.11, 3.12)"]
        docs["Documentation Check<br/>(config_readable.yml)"]
    end

    subgraph gate["PR Gate"]
        pr_check["Check PR Status<br/>& Profiler Label"]
    end

    subgraph integration["Integration Testing (GitHub Runner)"]
        setup["Setup Python 3.10.17<br/>+ pinned dependencies"]
        run_test["Run Scout Workflow<br/>(ecm_prep → run)"]
        compare["Compare Results vs Master<br/>(approx JSON, pixel-diff PDFs)"]
        convert["Convert Changed PDFs → PNGs<br/>(new + baseline)"]
        upload["Upload Artifacts"]
        commit_results["Commit Results to Branch"]
        fail_check{"Results<br/>differ?"}
        baseline_label{"update-baseline<br/>label?"}
        fail["❌ Fail"]
        warn["⚠️ Warn (accept)"]
        pass["✅ Pass"]
    end

    subgraph comment["PR Comment"]
        post_comment["Post/Update PR Comment<br/>with status + before/after plots"]
    end

    trigger --> lint & unit & docs
    lint & unit & docs --> pr_check
    pr_check --> setup
    setup --> run_test
    run_test --> compare
    compare --> convert
    convert --> upload
    upload --> commit_results
    commit_results --> fail_check
    fail_check -- "No" --> pass
    fail_check -- "Yes" --> baseline_label
    baseline_label -- "Yes" --> warn
    baseline_label -- "No" --> fail
    fail_check --> post_comment
    pass --> post_comment
    warn --> post_comment
    fail --> post_comment

    subgraph profiler["Optional: Profiler"]
        psrecord["psrecord<br/>(memory + CPU tracking)"]
    end

    run_test -. "run-profiler label<br/>or push to master" .-> psrecord

    style fail fill:#ff6b6b,color:#fff
    style warn fill:#ffd93d,color:#333
    style pass fill:#6bcb77,color:#fff
    style trigger fill:#4d96ff,color:#fff
```

## How It Works

### Triggers
- **Push to `master`**: Runs full pipeline including profiler
- **PR to `master`**: Runs on `opened`, `synchronize`, `reopened`, `ready_for_review`, `labeled`

### Comparison Strategy
- **JSON results**: Approximate comparison — values within `0.0001%` tolerance are treated as equal (handles floating-point platform noise)
- **PDF plots**: Rendered to PNG at 150 DPI and compared pixel-by-pixel — metadata-only differences (timestamps, version strings) are ignored
- **Summary Excel files**: Percent difference report generated for review

### When Results Differ
1. Results are committed to the PR branch and uploaded as artifacts
2. Before/after plot images are embedded in the PR comment
3. The integration test step fails with ❌

### Accepting Expected Changes
1. Add the `update-baseline` label to the PR
2. CI re-runs automatically (via `labeled` trigger)
3. The failure step is skipped — results are accepted as the new baseline
4. When merged, the committed results become the master baseline

### Pinned Environment
- Python `3.10.17` + `.github/constraints.txt` with exact dependency versions
- `SOURCE_DATE_EPOCH=0` for deterministic PDF timestamps
