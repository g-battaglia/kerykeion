# Contributing to Kerykeion

Thank you for your interest in contributing to Kerykeion! Contributions of all kinds are welcome: bug reports, feature requests, documentation improvements, and code changes.

## Getting Started

1. Fork the repository and clone it locally:

   ```bash
   git clone https://github.com/<your-username>/kerykeion.git
   cd kerykeion
   ```

2. Install the development dependencies (requires [uv](https://docs.astral.sh/uv/)):

   ```bash
   uv sync --dev
   ```

3. Create a new branch for your changes:

   ```bash
   git checkout -b my-feature
   ```

4. Make your changes, add tests if applicable, and ensure the test suite passes:

   ```bash
   uv run pytest
   ```

   The suite auto-detects the range of the installed ephemeris kernel and
   skips tests that need a wider one, so a plain run is green out of the box.
   With the full-range DE441 kernel installed you can force everything with
   `uv run pytest --tier=extended`.

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

By submitting a pull request or any other contribution to this repository, you agree to the following terms in respect of every contribution you have made and will make to the project:

1. **Copyright Assignment.** You hereby irrevocably assign to the project maintainer, **Giacomo Battaglia** ("Maintainer"), all right, title, and interest in the copyright of your past, present, and future contributions to this repository. To the extent any such assignment is not effective under applicable law, you instead grant the Maintainer a worldwide, perpetual, irrevocable, royalty-free, exclusive licence to use, reproduce, modify, distribute, sublicense, and re-license those contributions, with the right to grant sublicenses through multiple tiers. The Maintainer in turn grants you a perpetual, worldwide, non-exclusive, royalty-free licence to use and re-license your own contribution for any purpose, so this assignment does not stop you from reusing your own work.

2. **Re-licensing.** The Maintainer may re-license the project — or any part of it, including your contribution — under any other license, whether open-source or proprietary, at their sole discretion.

3. **AGPL Availability.** The project will continue to be publicly available under the AGPL-3.0 license. The copyright assignment enables dual-licensing and commercial offerings that help sustain long-term development.

4. **Moral rights.** To the fullest extent permitted by applicable law, you agree not to assert or enforce, against the Maintainer or its licensees, any moral rights you may hold in your contributions; where such rights are waivable, you waive them. Some jurisdictions (including Italy) treat certain moral rights as inalienable; this clause applies only as far as the law allows.

5. **Attribution.** Your authorship is acknowledged in the Git commit history, in the AUTHORS file, and, where appropriate, in release notes. Copyright assignment does not erase your credit as the original author of your contribution.

6. **Originality & authority.** You represent that each contribution is your original work, that you have the right to assign its copyright (and, where you contribute in the course of employment, that you have your employer's authorization to do so), and that the contribution does not knowingly infringe any third party's rights. If any part of your contribution is subject to a third-party license, you must clearly state this in the pull request.

7. **Governing law.** This agreement is governed by the laws of Italy, without regard to its conflict-of-laws rules, and the courts of the Maintainer's place of residence shall have jurisdiction, without prejudice to any mandatory protections available to you under your local law.

Your agreement is given by your own act of submitting a contribution (as stated above). On GitHub, a CLA-bot additionally checks each pull request and comments with instructions if your account is not yet recorded as having agreed; this automated check runs on GitHub only (it does not run on any mirror).

## Questions?

If you have any questions about contributing or the CLA, feel free to reach out at [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com?subject=Contributing).
