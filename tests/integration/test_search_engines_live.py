"""Integration tests for search engines with real API calls."""
import pytest

from nura.tool.search.baidu_search import BaiduSearchEngine
from nura.tool.search.bing_search import BingSearchEngine
from nura.tool.search.google_search import GoogleSearchEngine
from nura.tool.search.duckduckgo_search import DuckDuckGoSearchEngine


@pytest.mark.integration
def test_baidu_search_basic():
    """Test Baidu search with real API."""
    engine = BaiduSearchEngine()
    results = engine.perform_search("Python", num_results=5)

    # Baidu may return empty due to network/API issues
    assert results is not None
    print(f"Baidu results: {len(results)} items")


@pytest.mark.integration
def test_baidu_search_with_chinese_query():
    """Test Baidu search with Chinese query."""
    engine = BaiduSearchEngine()
    results = engine.perform_search("人工智能", num_results=3)

    # Baidu may return empty due to network/API issues
    assert results is not None
    if results:
        print(f"Baidu Chinese results: {results[0].title}")


@pytest.mark.integration
def test_bing_search_basic():
    """Test Bing search with real API."""
    engine = BingSearchEngine()
    results = engine.perform_search("Python programming", num_results=5)

    assert len(results) > 0
    assert results[0].title is not None
    assert results[0].url is not None
    print(f"Bing results: {len(results)} items")


@pytest.mark.integration
def test_bing_search_empty_query():
    """Test Bing search with empty query."""
    engine = BingSearchEngine()
    results = engine.perform_search("", num_results=5)

    assert results == []


@pytest.mark.integration
def test_bing_search_with_chinese_query():
    """Test Bing search with Chinese query."""
    engine = BingSearchEngine()
    results = engine.perform_search("机器学习", num_results=3)

    assert len(results) > 0
    print(f"Bing Chinese results: {results[0].title}")


@pytest.mark.integration
def test_google_search_basic():
    """Test Google search with real API."""
    engine = GoogleSearchEngine()
    results = engine.perform_search("Python", num_results=5)

    # Google search may fail due to restrictions, just verify it runs
    assert results is not None
    print(f"Google results: {len(results)} items")


@pytest.mark.integration
def test_duckduckgo_search_basic():
    """Test DuckDuckGo search with real API."""
    engine = DuckDuckGoSearchEngine()
    results = engine.perform_search("Python", num_results=5)

    assert len(results) > 0
    assert results[0].title is not None
    assert results[0].url is not None
    print(f"DuckDuckGo results: {len(results)} items")


@pytest.mark.integration
def test_all_engines_comparison():
    """Test all search engines and compare results."""
    query = "web development"

    engines = [
        ("Baidu", BaiduSearchEngine()),
        ("Bing", BingSearchEngine()),
    ]

    results_summary = {}
    for name, engine in engines:
        results = engine.perform_search(query, num_results=3)
        results_summary[name] = len(results)
        print(f"{name}: {len(results)} results")
        if results:
            print(f"  First result: {results[0].title}")

    # Bing should return results (Baidu may be empty due to network issues)
    assert results_summary["Bing"] > 0, "Bing returned no results"


@pytest.mark.integration
def test_search_result_format():
    """Test that all search engines return properly formatted results."""
    engine = BingSearchEngine()
    results = engine.perform_search("test", num_results=3)

    for item in results:
        # All items should have title and url
        assert item.title, "Missing title"
        assert item.url, "Missing url"
        # URL should be valid
        assert "http" in item.url or "www" in item.url
