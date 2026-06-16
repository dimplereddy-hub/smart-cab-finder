from unittest.mock import MagicMock, patch

import pytest

from gitlab_compliance_checker.ui.compliance import render_project_compliance_details


@pytest.fixture
def mock_gl():
    return MagicMock()


class DummyColumn:
    def __init__(self):
        self.metric = MagicMock()
        self.write = MagicMock()
        self.markdown = MagicMock()
        self.caption = MagicMock()
        self.__enter__ = MagicMock(return_value=self)
        self.__exit__ = MagicMock(return_value=False)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.fixture
def mock_streamlit():
    with patch("gitlab_compliance_checker.ui.compliance.st") as mock_st:
        mock_st.subheader = MagicMock()
        mock_st.metric = MagicMock()
        mock_st.json = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.text_input = MagicMock(return_value="")
        mock_st.button = MagicMock(return_value=False)
        mock_st.warning = MagicMock()
        mock_st.error = MagicMock()
        mock_st.write = MagicMock()
        mock_st.tabs = MagicMock(return_value=[DummyColumn()] * 6)

        def _columns(spec, *a, **k):
            n = spec if isinstance(spec, int) else len(spec)
            return [DummyColumn() for _ in range(n)]

        mock_st.columns = MagicMock(side_effect=_columns)
        mock_st.spinner = MagicMock()
        mock_st.spinner.return_value.__enter__ = MagicMock()
        mock_st.spinner.return_value.__exit__ = MagicMock()
        mock_st.expander = MagicMock()
        mock_st.expander.return_value.__enter__ = MagicMock()
        mock_st.expander.return_value.__exit__ = MagicMock()
        mock_st.success = MagicMock()
        yield mock_st


class TestRenderProjectCompliance:
    """Tests for render_project_compliance_details function."""

    @patch("gitlab_compliance_checker.ui.compliance.get_dx_suggestions")
    def test_renders_metrics(self, mock_suggestions, mock_gl, mock_streamlit):
        """Test that metrics are rendered."""
        report = {
            "dx_score": 85,
            "tools": {"project_type": "Python", "quality_tools": {}, "security": {}, "testing": {}, "automation": {}},
            "license": {"valid": True},
            "readme": {"needs_improvement": False},
            "metadata": {"description_present": True, "tags_present": True},
            "docs": {"files": {}, "all_present": True, "missing": []},
            "repo_files": {"files": {}, "all_present": True, "missing": [], "score": 100},
            "precommit": None,
            "dx_ci": None,
        }
        mock_suggestions.return_value = []

        render_project_compliance_details(report)

        # columns(4) is called for the summary metrics row
        calls = [c.args[0] for c in mock_streamlit.columns.call_args_list]
        assert 4 in calls, f"Expected columns(4) among calls, got: {calls}"
