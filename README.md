<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD013 -->
<h1 align="center">DefaultPoetry 📚✨</h1>
<p align="center">
  <img src="https://img.shields.io/badge/License-LGPLv3-blue.svg" alt="License: LGPL-3.0">
  <img src="https://img.shields.io/github/stars/Nachtalb/defaultpoetry?style=social" alt="GitHub Stars">
  <img src="https://img.shields.io/github/forks/Nachtalb/defaultpoetry?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/issues/Nachtalb/defaultpoetry" alt="GitHub Issues">
  <img src="https://img.shields.io/github/issues-pr/Nachtalb/defaultpoetry" alt="GitHub Pull Requests">
  <br>
  <a href="https://github.com/Nachtalb"><img src="https://img.shields.io/badge/Author-Nachtalb-1f425f.svg" alt="Author: Nachtalb"></a>
</p>

---

Streamline your Python project setup with DefaultPoetry - a tool designed to
quickly scaffold projects with best practices in coding standards,
configurations, and dependencies. Perfect for developers looking to jump-start
their projects with pre-configured settings for black, isort, mypy, pytest,
ruff, and more.

## 🚀 Quickstart

**Prerequisites:** Python 3.12 or higher.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Nachtalb/defaultpoetry
   cd defaultpoetry
   ```

2. **Install using Poetry:** `poetry install`

3. **Run the script directly:** `poetry run defaultpoetry -h`

---

## 🔧 Configuration

`defaultpoetry` uses the `templates` directory for its default configuration,
including but not limited to configurations for black, isort, mypy, pytest, and
ruff, as well as Prettier for README and JS files.

---

## 🛠️ Commands

- **init:** Initializes a new project with default configurations.
- **update:** Updates dependencies and pre-commit hooks.
- **install:** Installs the default configuration into an existing project.

---

## 📝 License

Licensed under the [LGPLv3 License](LICENSE).
