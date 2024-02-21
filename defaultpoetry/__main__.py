# PYTHON_ARGCOMPLETE_OK
import argparse
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any, Callable, Generator

import argcomplete
import tomlkit

DEFAULT_CONFIGURATION_PATH = Path(__file__).parent.parent / "templates"


class colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def _print(text: str, color: str, indent: int = 0, new_line: bool = True) -> None:
        indent_str = "  " * indent
        print(f"{indent_str}{color}{text}{colors.RESET}", end="\n" if new_line else "")

    @staticmethod
    def print_info(text: str, indent: int = 0, new_line: bool = True) -> None:
        colors._print(text, colors.CYAN, indent, new_line)

    @staticmethod
    def print_warning(text: str, indent: int = 0, new_line: bool = True) -> None:
        colors._print(text, colors.ORANGE, indent, new_line)

    @staticmethod
    def print_error(text: str, indent: int = 0, new_line: bool = True) -> None:
        colors._print(text, colors.RED, indent, new_line)

    @staticmethod
    def print_normal(text: str, indent: int = 0, new_line: bool = True) -> None:
        colors._print(text, colors.RESET, indent, new_line)

    @staticmethod
    def print_bold(text: str, indent: int = 0, new_line: bool = True) -> None:
        colors._print(text, colors.BOLD, indent, new_line)

    @staticmethod
    def print_underline(text: str, indent: int = 0, new_line: bool = True) -> None:
        colors._print(text, colors.UNDERLINE, indent, new_line)

    @staticmethod
    def print_header(text: str, indent: int = 0, new_line: bool = True) -> None:
        colors._print(text, colors.HEADER, indent, new_line)


def _run_shell_command(command: list[str], path: Path, print_error: bool = True) -> bool:
    try:
        colors.print_normal("Running command: ", indent=1, new_line=False)
        colors.print_info(f"{' '.join(command)}")

        run(command, cwd=path, check=True)
        return True
    except CalledProcessError as e:
        if print_error:
            colors.print_error(f"Failed to run \"{' '.join(command)}\": {e}")
        return False


def _run_poetry_init(path: Path) -> None:
    print("Initializing poetry")
    _run_shell_command(["poetry", "init", "--no-interaction"], path)


def _create_default_project_structure(path: Path) -> None:
    print("Creating default project structure")

    readme = path / "README.md"
    if not readme.exists():
        colors.print_normal("Creating ", indent=1, new_line=False)
        colors.print_info("README.md")
        readme.write_text("# Project Title")

    pyproject = path / "pyproject.toml"
    config = tomlkit.loads(pyproject.read_text())
    project_name: str = config["tool"]["poetry"]["name"]

    code_directory = path / project_name
    if not code_directory.exists():
        colors.print_normal("Creating code directory ", indent=1, new_line=False)
        colors.print_info(project_name)
        code_directory.mkdir()

    init_file = code_directory / "__init__.py"
    if not init_file.exists():
        colors.print_normal("Creating ", indent=1, new_line=False)
        colors.print_info(f"{project_name}/__init__.py")
        init_file.touch()

    test_directory = path / "tests"
    if not test_directory.exists():
        colors.print_normal("Creating test directory ", indent=1, new_line=False)
        colors.print_info("tests")
        test_directory.mkdir()


def _run_pre_commit_init(path: Path) -> None:
    print("Initializing pre-commit")
    _run_shell_command(["poetry", "run", "pre-commit", "install"], path)


def _run_poetry_install(path: Path) -> None:
    print("Running poetry install")
    _run_shell_command(["poetry", "install"], path)


def _toml_is_same_type(a: Any, b: Any) -> bool:
    if hasattr(a, "unwrap"):
        a = a.unwrap()
    if hasattr(b, "unwrap"):
        b = b.unwrap()

    return isinstance(a, type(b))


def _key(parent_key: str, key: str) -> str:
    return (f"{parent_key}.{key}" if parent_key else key).lstrip(".")


def _deep_merge_tomldocs(
    target: tomlkit.TOMLDocument | tomlkit.container.OutOfOrderTableProxy | tomlkit.items.Table,
    source: tomlkit.TOMLDocument | tomlkit.container.OutOfOrderTableProxy | tomlkit.items.Table,
    force: bool = False,
    parent_key: str = "",
) -> None:
    for key, new_value in source.items():
        current_value = target.get(key, None)

        if not _toml_is_same_type(new_value, current_value):
            if current_value is not None and not force:
                colors.print_warning(
                    f"Key {_key(parent_key, key)} type mismatch source: {type(new_value)} target: {type(current_value)}, use --force to overwrite",
                    indent=2,
                )
                continue
            target[key] = new_value

        elif isinstance(new_value, tomlkit.items.AoT | tomlkit.items.Array):
            current_values = [item.unwrap() for item in current_value]
            for item in new_value:
                if item.unwrap() not in current_values:
                    current_value.append(item)

        elif isinstance(new_value, tomlkit.TOMLDocument | tomlkit.container.OutOfOrderTableProxy | tomlkit.items.Table):
            if current_value is None:
                target[key] = new_value
            else:
                _deep_merge_tomldocs(current_value, new_value, force=force, parent_key=f"{parent_key}.{key}")

        elif key in target and not force:
            colors.print_warning(f"Key {_key(parent_key, key)} already exists, use --force to overwrite", indent=2)
            continue

        else:
            target[key] = new_value


def _install_pyproject_toml(file: Path, target: Path, force: bool) -> None:
    colors.print_normal("Merging pyproject.toml", indent=1)
    current_config = tomlkit.loads(target.read_text())
    default_config = tomlkit.loads(file.read_text())

    _deep_merge_tomldocs(current_config, default_config, force=force)

    target.write_text(tomlkit.dumps(current_config))


def _install_default_dev_dependencies(path: Path) -> None:
    print("Installing default dev dependencies")
    _run_shell_command(
        [
            "poetry",
            "add",
            "--group",
            "dev",
            "black",
            "ruff",
            "ruff-lsp",
            "mypy",
            "isort",
            "ipdb",
            "pre-commit",
            "pytest",
        ],
        path,
    )


def _install_default_configuration(config_path: Path, path: Path, force: bool = False) -> None:
    print("Installing default configuration")
    for file in config_path.glob("*"):
        target = path / file.name

        if file.name == "pyproject.toml":
            _install_pyproject_toml(file, target, force)
            continue

        if file.is_file():
            if force or not target.exists():
                if force and target.exists():
                    colors.print_warning("Overwriting ", indent=1, new_line=False)
                else:
                    colors.print_normal("Installing ", indent=1, new_line=False)
                colors.print_info(file.name)
                target.write_text(file.read_text())
            else:
                colors.print_warning(f"File {target} already exists, skipping. Use --force to overwrite")


def _run_pre_commit_install_hooks(path: Path) -> None:
    print("Installing pre-commit hooks")
    _run_shell_command(["poetry", "run", "pre-commit", "install-hooks"], path)


def _git_init(path: Path) -> None:
    print("Initializing git")
    _run_shell_command(["git", "init"], path)


@contextmanager
def _git_stash(path: Path) -> Generator[None, None, None]:
    _run_shell_command(["git", "stash", "--all"], path)
    try:
        yield
    finally:
        _run_shell_command(["git", "stash", "pop"], path)


@contextmanager
def _conditional_context_manager(condition: bool, context_manager: Callable[..., Any]) -> Generator[Any, None, None]:
    if condition:
        yield context_manager
    else:
        yield


def _git_commit(path: Path, message: str) -> None:
    print("Committing files")
    _run_shell_command(["git", "add", "."], path)
    if not _run_shell_command(["git", "diff", "--cached", "--exit-code", "--quiet"], path, print_error=False):
        _run_shell_command(["git", "commit", "-m", message], path)
    else:
        colors.print_warning("No changes to commit", indent=1)


def init(args: argparse.Namespace) -> None:
    colors.print_header("Initializing project")
    path = args.path

    if path.exists():
        colors.print_error(f"Path {path} already exists, use install command to install default configuration")
        return

    path.mkdir(parents=True, exist_ok=True)

    _run_poetry_init(path)
    _create_default_project_structure(path)
    _install_default_configuration(args.configuration, path, force=args.force)
    _install_default_dev_dependencies(path)
    _run_poetry_install(path)
    _run_pre_commit_init(path)
    _run_pre_commit_install_hooks(path)

    if not args.no_git:
        _git_init(path)

    if not args.no_git and not args.no_commit:
        _git_commit(path, "Initial commit")


def update(args: argparse.Namespace) -> None:
    colors.print_header("Updating project")
    try:
        _run_shell_command(["poetry", "update"], args.path)
    except CalledProcessError as e:
        colors.print_error(f"Failed to run poetry update: {e}")

    try:
        _run_shell_command(["poetry", "run", "pre-commit", "autoupdate"], args.path)
    except CalledProcessError as e:
        colors.print_error(f"Failed to run pre-commit autoupdate: {e}")


def install(args: argparse.Namespace) -> None:
    colors.print_header("Installing default configuration")
    if not args.path.exists():
        colors.print_error(f"Path {args.path} does not exist, use init command to initialize the project")
        return

    is_git = (args.path / ".git").exists()

    with _conditional_context_manager(is_git, _git_stash(args.path)):
        _install_default_configuration(args.configuration, args.path, force=args.force)
        _create_default_project_structure(args.path)
        _install_default_dev_dependencies(args.path)
        _run_poetry_install(args.path)
        _run_pre_commit_init(args.path)
        _run_pre_commit_install_hooks(args.path)

        if is_git and not args.no_commit:
            _git_commit(args.path, "Install python poetry default configuration")


def _save_exit[T](func: T) -> T:  # type: ignore[valid-type, name-defined]
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\nExiting")
            exit(1)

    return wrapper


@_save_exit
def main() -> None:
    parser = argparse.ArgumentParser(description="Setup poetry default configuration")
    subparsers = parser.add_subparsers()

    # sub commands with subparsers
    # init - initialize the project from scratch including our default configuration
    # update - update the project (poetry, pre-commit, etc)
    # install - install our default configuration into an existing project

    init_parser = subparsers.add_parser("init", help="Initialize the project from scratch")
    init_parser.set_defaults(func=init)
    init_parser.add_argument("path", type=Path, help="The path to the project")
    init_parser.add_argument(
        "-c",
        "--configuration",
        type=Path,
        default=DEFAULT_CONFIGURATION_PATH,
        help="The path to the default configuration",
    )
    init_parser.add_argument("-G", "--no-git", action="store_true", help="Do not initialize git")
    init_parser.add_argument("-C", "--no-commit", action="store_true", help="Do not commit the initial files")

    update_parser = subparsers.add_parser("update", help="Update the project")
    update_parser.set_defaults(func=update)
    update_parser.add_argument("path", type=Path, help="The path to the project")

    install_parser = subparsers.add_parser("install", help="Install the default configuration into an existing project")
    install_parser.set_defaults(func=install)
    install_parser.add_argument("path", type=Path, help="The path to the project")
    install_parser.add_argument(
        "-c",
        "--configuration",
        type=Path,
        default=DEFAULT_CONFIGURATION_PATH,
        help="The path to the default configuration",
    )
    install_parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files")
    install_parser.add_argument("-C", "--no-commit", action="store_true", help="Do not commit the initial files")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
