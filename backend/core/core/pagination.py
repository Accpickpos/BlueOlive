"""
Custom pagination classes for API responses.
"""

from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """Custom pagination that supports page_size query parameter."""

    page_size_query_param = "page_size"
    page_size_query_description = "Number of results to return per page"
    max_page_size = 100
