from django.urls import path, include
from rest_framework.routers import DefaultRouter
from wiki_stream_app.views import WikipediaEditViewSet

# Create a router for the ViewSet
router = DefaultRouter()
router.register(r'', WikipediaEditViewSet)

urlpatterns = [
    # API 1, 2, 3: Handles LIST (filtered), RETRIEVE, UPDATE, DELETE
    # e.g., GET /api/edits/?user=Example, GET/PUT/DELETE /api/edits/1/
    path('', include(router.urls)),

    # API 4: Handles Bulk Delete (POST /api/edits/bulk-delete/)
    # The bulk_delete_by_criteria is registered via the router as a custom action
]
