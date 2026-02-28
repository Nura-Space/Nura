"""Tests for search engine modules."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from nura.tool.search.base import SearchItem, WebSearchEngine
from nura.tool.search.bing_search import BingSearchEngine
from nura.tool.search.google_search import GoogleSearchEngine
from nura.tool.search.duckduckgo_search import DuckDuckGoSearchEngine


class TestSearchItem:
    """Test cases for SearchItem."""

    @pytest.mark.unit
    def test_create_search_item(self):
        """Test creating a SearchItem."""
        item = SearchItem(
            title="Test Title",
            url="https://example.com",
            description="Test description"
        )

        assert item.title == "Test Title"
        assert item.url == "https://example.com"
        assert item.description == "Test description"

    @pytest.mark.unit
    def test_create_search_item_with_null_description(self):
        """Test creating SearchItem with null description."""
        item = SearchItem(
            title="Test Title",
            url="https://example.com"
        )

        assert item.description is None

    @pytest.mark.unit
    def test_str_representation(self):
        """Test string representation."""
        item = SearchItem(
            title="Test Title",
            url="https://example.com"
        )

        assert str(item) == "Test Title - https://example.com"


class TestWebSearchEngine:
    """Test cases for WebSearchEngine base class."""

    @pytest.mark.unit
    def test_base_class_is_abstract(self):
        """Test that base class cannot be instantiated directly."""
        with pytest.raises(NotImplementedError):
            engine = WebSearchEngine()
            engine.perform_search("test")


class TestBingSearchEngine:
    """Test cases for BingSearchEngine."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test BingSearchEngine initialization."""
        engine = BingSearchEngine()
        assert engine is not None
        assert engine.session is not None

    @pytest.mark.unit
    def test_search_with_empty_query(self):
        """Test search with empty query."""
        engine = BingSearchEngine()

        results = engine.perform_search("", num_results=5)

        assert results == []

    @pytest.mark.unit
    def test_search_sync_with_mock_html(self):
        """Test _search_sync with mocked HTML response."""
        engine = BingSearchEngine()

        # Mock HTML response
        mock_html = """
        <html>
            <ol id="b_results">
                <li class="b_algo">
                    <h2><a href="https://example1.com">Title 1</a></h2>
                    <p>Description 1</p>
                </li>
                <li class="b_algo">
                    <h2><a href="https://example2.com">Title 2</a></h2>
                    <p>Description 2</p>
                </li>
            </ol>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.encoding = "utf-8"

        with patch.object(engine.session, 'get', return_value=mock_response):
            results = engine._search_sync("test", num_results=5)

            assert len(results) >= 1
            assert results[0].title == "Title 1"
            assert results[0].url == "https://example1.com"

    @pytest.mark.unit
    def test_parse_html_with_no_results(self):
        """Test parsing HTML with no results."""
        engine = BingSearchEngine()

        mock_html = "<html><body>No results</body></html>"
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.encoding = "utf-8"

        with patch.object(engine.session, 'get', return_value=mock_response):
            results, next_url = engine._parse_html("https://bing.com/search?q=test")

            assert results == []
            assert next_url is None

    @pytest.mark.unit
    def test_parse_html_with_exception(self):
        """Test parsing HTML with exception."""
        engine = BingSearchEngine()

        with patch.object(engine.session, 'get', side_effect=Exception("Network error")):
            results, next_url = engine._parse_html("https://bing.com/search?q=test")

            assert results == []
            assert next_url is None

    @pytest.mark.unit
    def test_parse_html_with_next_page(self):
        """Test parsing HTML with next page link."""
        engine = BingSearchEngine()

        mock_html = """
        <html>
            <ol id="b_results">
                <li class="b_algo">
                    <h2><a href="https://example1.com">Title 1</a></h2>
                    <p>Description 1</p>
                </li>
            </ol>
            <a title="Next page" href="/search?q=test&first=11">Next</a>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.encoding = "utf-8"

        with patch.object(engine.session, 'get', return_value=mock_response):
            results, next_url = engine._parse_html("https://bing.com/search?q=test")

            assert len(results) >= 1
            assert next_url is not None

    @pytest.mark.unit
    def test_parse_html_truncates_long_description(self):
        """Test that long descriptions are truncated."""
        engine = BingSearchEngine()

        # Create a very long description
        long_desc = "A" * 500

        mock_html = f"""
        <html>
            <ol id="b_results">
                <li class="b_algo">
                    <h2><a href="https://example1.com">Title 1</a></h2>
                    <p>{long_desc}</p>
                </li>
            </ol>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.encoding = "utf-8"

        with patch.object(engine.session, 'get', return_value=mock_response):
            results, _ = engine._parse_html("https://bing.com/search?q=test")

            assert len(results) >= 1
            # Should be truncated to 300 chars
            assert len(results[0].description) <= 300

    @pytest.mark.unit
    def test_parse_html_missing_h2(self):
        """Test parsing HTML with missing h2 tag."""
        engine = BingSearchEngine()

        mock_html = """
        <html>
            <ol id="b_results">
                <li class="b_algo">
                    <p>Description without title</p>
                </li>
            </ol>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.encoding = "utf-8"

        with patch.object(engine.session, 'get', return_value=mock_response):
            results, _ = engine._parse_html("https://bing.com/search?q=test")

            # Should have fallback title
            assert len(results) >= 1


class TestGoogleSearchEngine:
    """Test cases for GoogleSearchEngine."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test GoogleSearchEngine initialization."""
        engine = GoogleSearchEngine()
        assert engine is not None


class TestDuckDuckGoSearchEngine:
    """Test cases for DuckDuckGoSearchEngine."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test DuckDuckGoSearchEngine initialization."""
        engine = DuckDuckGoSearchEngine()
        assert engine is not None
