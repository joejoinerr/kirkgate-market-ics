from pathlib import Path

import utils


class TestGetProjectRoot:
    """Tests for the get_project_root function."""

    def test_returns_path_object(self) -> None:
        """Tests that the function returns a Path object."""
        result = utils.get_project_root()
        assert isinstance(result, Path)

    def test_returns_absolute_path(self) -> None:
        """Tests that the returned path is absolute."""
        result = utils.get_project_root()
        assert result.is_absolute()

    def test_returns_correct_root_directory(self, monkeypatch) -> None:
        """Tests that the function returns the correct root directory."""
        monkeypatch.setattr(utils, "__file__", "/home/test/test-project/src/utils.py")
        expected = Path("/home/test/test-project")
        result = utils.get_project_root()
        assert result == expected

    def test_returns_correct_real_project_structure(self) -> None:
        """Tests that the function works with the real project structure."""
        expected = Path(__file__).parent.parent
        result = utils.get_project_root()
        assert result == expected
