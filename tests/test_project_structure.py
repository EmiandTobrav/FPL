from pathlib import Path


REQUIRED_DIRECTORIES = [
    "data/raw",
    "data/interim",
    "data/processed",
    "data/predictions",
    "notebooks",
    "src/data",
    "src/features",
    "src/models",
    "src/evaluation",
    "tests",
    "reports",
]


def test_required_project_directories_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    missing = [
        directory
        for directory in REQUIRED_DIRECTORIES
        if not (root / directory).is_dir()
    ]

    assert missing == []
