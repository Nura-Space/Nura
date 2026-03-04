"""Tests for web search module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from nura.tool.web_search import (
    SearchResult,
    SearchMetadata,
    SearchResponse,
    WebContentFetcher,
)


class TestSearchResult:
    """Test cases for SearchResult."""

    @pytest.mark.unit
    def test_create_search_result(self):
        """Test creating a search result."""
        result = SearchResult(
            position=1,
            url="https://example.com",
            title="Example Title",
            description="Example description",
            source="google",
        )

        assert result.position == 1
        assert result.url == "https://example.com"
        assert result.title == "Example Title"
        assert result.description == "Example description"
        assert result.source == "google"
        assert result.raw_content is None

    @pytest.mark.unit
    def test_create_search_result_with_raw_content(self):
        """Test creating search result with raw content."""
        result = SearchResult(
            position=1,
            url="https://example.com",
            title="Example",
            description="Description",
            source="bing",
            raw_content="Raw content here",
        )

        assert result.raw_content == "Raw content here"

    @pytest.mark.unit
    def test_str_representation(self):
        """Test string representation."""
        result = SearchResult(
            position=1,
            url="https://example.com",
            title="Example Title",
            description="Description",
            source="google",
        )

        assert str(result) == "Example Title (https://example.com)"

    @pytest.mark.unit
    def test_str_representation_empty_title(self):
        """Test string representation with empty title."""
        result = SearchResult(
            position=1,
            url="https://example.com",
            title="",
            description="Description",
            source="google",
        )

        assert "https://example.com" in str(result)


class TestSearchMetadata:
    """Test cases for SearchMetadata."""

    @pytest.mark.unit
    def test_create_metadata(self):
        """Test creating search metadata."""
        metadata = SearchMetadata(total_results=100, language="en", country="US")

        assert metadata.total_results == 100
        assert metadata.language == "en"
        assert metadata.country == "US"


class TestSearchResponse:
    """Test cases for SearchResponse."""

    @pytest.mark.unit
    def test_create_response(self):
        """Test creating a search response."""
        response = SearchResponse(query="test query", results=[], error=None)

        assert response.query == "test query"
        assert response.results == []
        assert response.metadata is None

    @pytest.mark.unit
    def test_response_with_error(self):
        """Test response with error field."""
        response = SearchResponse(query="test", error="Some error occurred")

        assert response.error == "Some error occurred"

    @pytest.mark.unit
    def test_response_populate_output_empty_results(self):
        """Test output population with empty results."""
        response = SearchResponse(query="test query", results=[], error=None)

        result = response.populate_output()

        assert "test query" in result.output

    @pytest.mark.unit
    def test_response_populate_output_with_results(self):
        """Test output population with search results."""
        results = [
            SearchResult(
                position=1,
                url="https://example.com",
                title="Example",
                description="A description",
                source="google",
            )
        ]

        response = SearchResponse(query="test", results=results, error=None)

        result = response.populate_output()

        assert "Example" in result.output
        assert "https://example.com" in result.output
        assert "A description" in result.output

    @pytest.mark.unit
    def test_response_populate_output_with_empty_title(self):
        """Test output with empty title."""
        results = [
            SearchResult(
                position=1,
                url="https://example.com",
                title="",
                description="A description",
                source="google",
            )
        ]

        response = SearchResponse(query="test", results=results, error=None)

        result = response.populate_output()

        assert "No title" in result.output

    @pytest.mark.unit
    def test_response_populate_output_with_raw_content(self):
        """Test output with raw content."""
        long_content = "A" * 2000  # More than 1000 chars

        results = [
            SearchResult(
                position=1,
                url="https://example.com",
                title="Example",
                description="Description",
                source="google",
                raw_content=long_content,
            )
        ]

        response = SearchResponse(query="test", results=results, error=None)

        result = response.populate_output()

        assert "Content:" in result.output
        assert "..." in result.output  # Should be truncated

    @pytest.mark.unit
    def test_response_populate_output_with_metadata(self):
        """Test output with metadata."""
        results = [
            SearchResult(
                position=1,
                url="https://example.com",
                title="Example",
                description="Description",
                source="google",
            )
        ]

        metadata = SearchMetadata(total_results=50, language="zh", country="CN")

        response = SearchResponse(
            query="测试", results=results, metadata=metadata, error=None
        )

        result = response.populate_output()

        assert "Metadata:" in result.output
        assert "50" in result.output
        assert "zh" in result.output
        assert "CN" in result.output

    @pytest.mark.unit
    def test_response_populate_output_with_error(self):
        """Test that error responses skip population."""
        response = SearchResponse(query="test", error="Some error")

        result = response.populate_output()

        assert result.error == "Some error"
        # Output may be empty or default

    @pytest.mark.unit
    def test_response_populate_output_description_stripping(self):
        """Test that descriptions are stripped."""
        results = [
            SearchResult(
                position=1,
                url="https://example.com",
                title="Example",
                description="  \n  Description with whitespace  \n  ",
                source="google",
            )
        ]

        response = SearchResponse(query="test", results=results, error=None)

        result = response.populate_output()

        # Should not have leading/trailing whitespace in output
        assert "Description with whitespace" in result.output


class TestWebContentFetcher:
    """Test cases for WebContentFetcher."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_content_success(self):
        """Test successful content fetching."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Test content</p></body></html>"

        with patch("nura.tool.web_search.requests.get", return_value=mock_response):
            content = await WebContentFetcher.fetch_content("https://example.com")

        assert content is not None
        assert "Test content" in content

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_content_non_200(self):
        """Test content fetching with non-200 status."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("nura.tool.web_search.requests.get", return_value=mock_response):
            content = await WebContentFetcher.fetch_content("https://example.com")

        assert content is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_content_exception(self):
        """Test content fetching with exception."""
        import requests

        with patch(
            "nura.tool.web_search.requests.get",
            side_effect=requests.RequestException("Network error"),
        ):
            content = await WebContentFetcher.fetch_content("https://example.com")

        assert content is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_content_removes_scripts(self):
        """Test that scripts and styles are removed."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head>
            <script>alert('bad');</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <nav>Navigation</nav>
            <p>Main content</p>
            <footer>Footer</footer>
        </body>
        </html>
        """

        with patch("nura.tool.web_search.requests.get", return_value=mock_response):
            content = await WebContentFetcher.fetch_content("https://example.com")

        assert content is not None
        assert "alert" not in content
        assert "Navigation" not in content
        assert "Footer" not in content
        assert "Main content" in content

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_content_empty_html(self):
        """Test content fetching with empty HTML."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>"

        with patch("nura.tool.web_search.requests.get", return_value=mock_response):
            content = await WebContentFetcher.fetch_content("https://example.com")

        assert content is None or content == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_content_with_timeout(self):
        """Test content fetching with custom timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Content</body></html>"

        with patch(
            "nura.tool.web_search.requests.get", return_value=mock_response
        ) as mock_get:
            await WebContentFetcher.fetch_content("https://example.com", timeout=5)

            # Verify timeout was passed
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs.get("timeout") == 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fetch_content_size_limit(self):
        """Test content size is limited to 10KB."""
        # Create content larger than 10KB
        long_content = "A" * 20000

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = f"<html><body><p>{long_content}</p></body></html>"

        with patch("nura.tool.web_search.requests.get", return_value=mock_response):
            content = await WebContentFetcher.fetch_content("https://example.com")

        assert content is not None
        assert len(content) <= 10050  # Some margin for HTML tags


@pytest.mark.unit
class TestWebSearchToolClass:
    """Test WebSearch tool class."""

    def test_web_search_creation(self):
        """Test creating a WebSearch tool."""
        from nura.tool.web_search import WebSearch

        tool = WebSearch()
        assert tool.name == "web_search"
        assert "search" in tool.description.lower()
        assert "query" in tool.parameters["properties"]

    def test_web_search_parameters(self):
        """Test WebSearch parameters schema."""
        from nura.tool.web_search import WebSearch

        tool = WebSearch()
        params = tool.parameters

        assert params["type"] == "object"
        assert "query" in params["required"]
        assert "query" in params["properties"]
        assert "num_results" in params["properties"]
        assert "lang" in params["properties"]
        assert "country" in params["properties"]
        assert "fetch_content" in params["properties"]

    @pytest.mark.asyncio
    async def test_execute_returns_search_response(self):
        """Test that execute returns SearchResponse."""
        from nura.tool.web_search import WebSearch

        tool = WebSearch()
        # Mock all search engines to return empty results, forcing error response
        # Also mock sleep to avoid long retry delays in tests
        with patch.object(
            tool, "_try_all_engines", new_callable=AsyncMock
        ) as mock_search:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                mock_search.return_value = []
                result = await tool.execute(query="test query")

                assert isinstance(result, SearchResponse)
                assert result.query == "test query"
                # Should return error response after all engines fail
                assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_with_results(self):
        """Test execute with search results."""
        from nura.tool.web_search import WebSearch

        tool = WebSearch()

        mock_results = [
            SearchResult(
                position=1,
                url="https://example.com",
                title="Example",
                description="An example page",
                source="google",
            )
        ]

        with patch.object(
            tool, "_try_all_engines", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = mock_results
            result = await tool.execute(query="test", num_results=5)

            assert isinstance(result, SearchResponse)
            assert result.query == "test"
            assert len(result.results) == 1
            assert result.results[0].title == "Example"

    @pytest.mark.asyncio
    async def test_execute_with_fetch_content(self):
        """Test execute with content fetching enabled."""
        from nura.tool.web_search import WebSearch

        tool = WebSearch()

        mock_results = [
            SearchResult(
                position=1,
                url="https://example.com",
                title="Example",
                description="An example page",
                source="google",
            )
        ]

        with patch.object(
            tool, "_try_all_engines", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = mock_results

            with patch.object(
                tool, "_fetch_content_for_results", new_callable=AsyncMock
            ) as mock_fetch:
                mock_fetch.return_value = mock_results
                result = await tool.execute(query="test", fetch_content=True)

                assert isinstance(result, SearchResponse)
                mock_fetch.assert_called_once()

    def test_to_param(self):
        """Test tool to param conversion."""
        from nura.tool.web_search import WebSearch

        tool = WebSearch()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "web_search"
        assert "parameters" in tool_dict["function"]
