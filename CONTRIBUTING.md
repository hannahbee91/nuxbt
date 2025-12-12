# Contributing to nuxbt

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing to `nuxbt`.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## I Have a Question

If you have questions, please search the open Issues to see if your question has already been answered. If not, feel free to open a new Issue with the "question" label.

## I Want To Contribute

### Reporting Bugs

This section guides you through submitting a bug report for `nuxbt`. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as many details as possible.
- **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for `nuxbt`, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title** for the issue to identify the suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
- **Explain why this enhancement would be useful** to most `nuxbt` users.

### Your First Code Contribution

#### Development Environment Setup

`nuxbt` uses [Poetry](https://python-poetry.org/) for dependency management and packaging.

1.  **Install Poetry**: Follow the instructions on the [official Poetry website](https://python-poetry.org/docs/#installation).
2.  **Install Dependencies**: Run the following command in the root of the repository to install the project dependencies:

    ```bash
    poetry install
    ```

#### Workflow

1.  **Fork the Repository**: Click the "Fork" button at the top right of the repository page.
2.  **Clone your Fork**:
    ```bash
    git clone git@github.com:<YOUR_USERNAME>/nuxbt.git
    cd nuxbt
    ```
3.  **Create a Branch**: Create a new branch for your feature or fix.
    ```bash
    git checkout -b feature/amazing-feature
    ```
4.  **Make Changes**: Make your code changes.
5.  **Commit Changes**:
    > [!IMPORTANT]
    > Please follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for your commit messages. This helps us generate changelogs and version releases automatically.

    Examples:
    - `feat: allow provided config object to align with other types`
    - `fix: handle empty response from server`
    - `docs: update CONTRIBUTING.md`

    ```bash
    git add .
    git commit -m "feat: add new feature"
    ```
6.  **Push Changes**:
    ```bash
    git push origin feature/amazing-feature
    ```
7.  **Open a Pull Request**: Go to the original repository and click "Compare & pull request".

Thank you for contributing!
