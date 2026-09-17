from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        next_link = self.get_next_link()
        previous_link = self.get_previous_link()
        return Response(
            {
                # Kept for backward compatibility with any existing consumer.
                "links": {
                    "next": next_link,
                    "previous": previous_link,
                },
                # The app reads these at the root (see explore-screen.tsx),
                # not nested under "links" — without this it can't tell
                # there's a next page once a filter is applied.
                "next": next_link,
                "previous": previous_link,
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        base_schema = super().get_paginated_response_schema(schema)
        base_schema["properties"]["links"] = {
            "type": "object",
            "properties": {
                "next": base_schema["properties"]["next"],
                "previous": base_schema["properties"]["previous"],
            },
        }
        return base_schema
