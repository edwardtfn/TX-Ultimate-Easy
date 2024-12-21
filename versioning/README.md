# Versioning

## Overview
This project uses a time-based versioning scheme: `year.month.sequential_number`.
This scheme makes it easy to identify when a version was released and provides a clear order for releases within a given month.

### Examples
- `2024.12.01` – First release of December 2024.
- `2024.12.02` – Second release of December 2024.
- `2025.01.01` – First release of January 2025.

## Files
- **`VERSION`**: Contains the current version of the project as plain text.
- **`bump_version.sh`**: A script to increment the version based on the current date and release sequence.
- **`README.md`**: Documentation for the versioning process.

## Versioning Rules
1. The version format is `YYYY.MM.NN`, where:
   - `YYYY` is the current year.
   - `MM` is the current month (two digits).
   - `NN` is the sequential release number within the month (starting at `01`).
2. On each new merge to the `main` branch:
   - If the month hasn’t changed, the sequential number (`NN`) is incremented.
   - If the month has changed, the sequential number resets to `01`.

## Usage

### Automatically Managed
The versioning process is fully integrated into the workflow. Developers do not need to manually increment or manage versions.
Simply push your changes, and the system will handle version updates and tagging automatically.

### Access Version in Code
The version is accessible in the ESPHome YAML configuration file (`TX-Ultimate-Easy-ESPHome_core.yaml`) using the following syntax:

```yaml
substitutions:
  version: <<: !include ../versioning/VERSION
```

This ensures the correct version is used directly in the ESPHome setup without requiring manual updates.

## Benefits of this Versioning Approach
1. **Clarity**: Each version is tied to a specific point in time, making it easy to track releases.
2. **Automation**: The process is seamless and reduces manual effort.
3. **Scalability**: Supports frequent releases while keeping the versioning system organized.
4. **Traceability**: Git tags and the `VERSION` file ensure releases are well-documented and easily accessible.

## Extending the System
- Add more scripts to handle additional automation tasks, such as generating changelogs or notifying stakeholders of new releases.
- Enhance the `bump_version.sh` script to support different versioning schemes if needed.
- Integrate versioning information into your deployment pipelines to label builds with their corresponding version.

### GitHub Actions Workflow Adjustment
The GitHub Actions workflow for versioning runs only when changes are merged into the `main` branch, ensuring no premature version updates during PR creation.
This behavior is automatically handled by the integrated workflow.
