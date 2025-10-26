import django_filters
from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
# UPDATED IMPORT PATH
from wiki_stream_app.models import WikipediaEdit


# --- 1. Serializer ---
class WikipediaEditSerializer(serializers.ModelSerializer):
    """Serializer for WikipediaEdit model."""

    class Meta:
        model = WikipediaEdit
        fields = '__all__'
        read_only_fields = ('edit_timestamp',)  # Prevent users from manually changing the creation time


# --- 2. Filters ---
class WikipediaEditFilter(django_filters.FilterSet):
    """Filter class for WikipediaEdit data."""

    # Filter 1: Filter by date range (e.g., /?start_date=2025-01-01&end_date=2025-01-31)
    start_date = django_filters.DateFilter(field_name='edit_timestamp', lookup_expr='date__gte')
    end_date = django_filters.DateFilter(field_name='edit_timestamp', lookup_expr='date__lte')

    # Filter 2: Filter by user (partial match)
    user = django_filters.CharFilter(field_name='user_name', lookup_expr='icontains')

    # Filter 3: Filter by article title (partial match)
    title = django_filters.CharFilter(field_name='article_title', lookup_expr='icontains')

    class Meta:
        model = WikipediaEdit
        fields = ['start_date', 'end_date', 'user', 'title']


# --- 3. ViewSet ---
class WikipediaEditViewSet(viewsets.ModelViewSet):
    """
    Provides all API functionality:
    1. List (with Filters) - GET /api/edits/
    2. Retrieve, Update, Delete - GET/PUT/PATCH/DELETE /api/edits/{id}/
    3. Bulk Delete by Criteria - POST /api/edits/bulk_delete/
    """
    queryset = WikipediaEdit.objects.all()
    serializer_class = WikipediaEditSerializer
    filterset_class = WikipediaEditFilter

    # API 1: List processed data with filters (handled by filterset_class)
    # The default List method (GET /api/edits/) handles this.

    # API 3: Update existing data
    # The default RetrieveUpdateDestroy methods (PUT/PATCH /api/edits/{id}/) handle this.

    # API 4: Delete data streamed on certain criteria (date, user, article title)
    # This is implemented as a custom action for bulk deletion.
    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete_by_criteria(self, request):
        """
        Deletes data based on criteria provided in the POST body.
        Example POST body:
        {
            "date": "YYYY-MM-DD",
            "user_name": "ExampleUser",
            "article_title": "Python"
        }
        """
        data = request.data
        filters = Q()

        # Date Filter
        if 'date' in data:
            # Assumes date format is 'YYYY-MM-DD'
            try:
                target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                filters &= Q(edit_timestamp__date=target_date)
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        # User Filter
        if 'user_name' in data:
            filters &= Q(user_name=data['user_name'])

        # Article Title Filter
        if 'article_title' in data:
            filters &= Q(article_title=data['article_title'])

        # Require at least one filter for bulk deletion safety
        if not filters:
            return Response({
                                "error": "Please provide at least one criteria (date, user_name, or article_title) for bulk deletion."},
                            status=400)

        # Execute the deletion
        qs = WikipediaEdit.objects.filter(filters)
        deleted_count, _ = qs.delete()

        return Response({
            "status": "success",
            "message": f"Successfully deleted {deleted_count} edits matching the criteria."
        })
