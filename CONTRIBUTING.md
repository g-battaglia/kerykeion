# Contributing to Kerykeion

Thank you for your interest in contributing to Kerykeion! Contributions of all kinds are welcome: bug reports, feature requests, documentation improvements, and code changes.

## Getting Started

1. Fork the repository and clone it locally:

   ```bash
   git clone https://github.com/<your-username>/kerykeion.git
   cd kerykeion
   ```

2. Install the development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

3. Create a new branch for your changes:

   ```bash
   git checkout -b my-feature
   ```

4. Make your changes, add tests if applicable, and ensure the test suite passes:

   ```bash
   pytest
   ```

5. Push your branch and open a Pull Request against the `main` branch.

## Reporting Issues

- Use the [GitHub Issues](https://github.com/g-battaglia/kerykeion/issues) tracker.
- Include a clear description of the problem, steps to reproduce, and the expected vs. actual behaviour.
- If relevant, include the Python version, OS, and Kerykeion version.

## Code Style

- Follow the existing code style in the project.
- Use [Ruff](https://docs.astral.sh/ruff/) for linting.
- Type annotations are encouraged.

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See the [LICENSE](LICENSE) file for the full text.

## Contributor License Agreement (CLA) — Copyright Assignment

By submitting a pull request or any other contribution to this repository, you agree to the following terms:

1. **Copyright Assignment.** You assign all right, title, and interest in the copyright of your contribution to the project maintainer, **Giacomo Battaglia** ("Maintainer").

2. **Re-licensing.** The Maintainer reserves the right to re-license the project — or any part of it, including your contribution — under any other license, whether open-source or proprietary, at their sole discretion.

3. **AGPL Availability.** The project will continue to be publicly available under the AGPL-3.0 license. The copyright assignment enables dual-licensing and commercial offerings that help sustain long-term development.

4. **Attribution.** Your authorship is acknowledged in the Git commit history and, where appropriate, in release notes. Copyright assignment does not erase your credit as the original author of your contribution.

5. **Originality.** You represent that each contribution is your original work and that you have the right to assign its copyright. If any part of your contribution is subject to a third-party license, you must clearly state this in the pull request.

A CLA-bot automatically checks every pull request. If you have not yet been added to the approved contributors list, the bot will comment on your PR with instructions. Once you have confirmed your agreement (typically by being added to the list), all future PRs will pass the check automatically.

## Questions?

If you have any questions about contributing or the CLA, feel free to reach out at [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com?subject=Contributing).
