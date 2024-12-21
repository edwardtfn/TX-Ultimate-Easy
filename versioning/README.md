# Versioning

## Overview
This project uses a time-based versioning scheme: `year.month.sequential_number`.  
The system automates version updates and tagging to ensure consistent, conflict-free management of releases.

### Examples
- `2024.1.1` – First release of January 2024.
- `2024.12.2` – Second release of December 2024.

## How It Works
1. **Temporary Branch Creation**: A unique branch is created for each workflow run.
2. **Version Update**: The workflow updates the `VERSION` and `VERSION_YAML` files using the current date and release sequence.
3. **Commit with Marker**: Changes are committed with a `[skip-versioning]` marker to prevent triggering the workflow again.
4. **Merge into Main**: The temporary branch is merged into `main`.
5. **Branch Cleanup**: The temporary branch is deleted after merging.

## Usage

### Automated Workflow
The versioning process is fully automated:
- Developers submit their changes as usual.
- The workflow handles version updates, tagging, and integration into `main`.
- No manual intervention is needed for versioning.

### Accessing the Version in Code
The version is accessible in the ESPHome YAML configuration file (`TX-Ultimate-Easy-ESPHome_core.yaml`) using the following syntax:

```yaml
substitutions:
  version: <<: !include ../versioning/VERSION
```

This ensures the correct version is dynamically included in the ESPHome setup.

## Benefits
- **Clarity**: Easily track when a release occurred with meaningful version numbers.
- **Automation**: Eliminates manual version management.
- **Scalability**: Supports frequent updates and concurrent workflows.
- **Traceability**: Maintains a clear history of changes through Git tags and version files.

## System Details

### Version Format
The format `year.month.sequential_number` includes:
- `year` (YYYY): A 4-digit number representing the year.
- `month` (M): A number from 1 to 12 (no leading zeros).
- `sequential_number`: A positive number incremented with each release in the same month.

### Validation Rules
The `bump_version.sh` script enforces strict validation:
- Year must be a 4-digit number.
- Month must be 1–12 without leading zeros.
- Sequence must be a positive number without leading zeros.

If validation fails, the workflow stops and provides an error message.

### GitHub Workflow
The workflow is triggered automatically when:
- Changes are pushed to `main`.
- Developers trigger it manually using the `workflow_dispatch` event.

The workflow avoids infinite loops by committing changes with the `[skip-versioning]` marker.

## Extending the System
Consider extending the system to:
- Automatically generate release notes or changelogs.
- Notify stakeholders when a new version is released.
- Integrate versioning information into deployment pipelines.

## FAQ
**Q: What happens if two workflows run concurrently?**  
A: Each workflow operates in its own temporary branch, avoiding conflicts.

**Q: Can I manually update the version?**  
A: Manual updates are not needed. The workflow ensures accurate, automated versioning.
