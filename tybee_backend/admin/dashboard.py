import json

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.safestring import mark_safe


def dashboard_callback(request, context):

    from users.models import User
    from local_places.models import LocalPlace, Category

    # Stats
    total_users = User.objects.count()
    total_places = LocalPlace.objects.count()
    total_categories = Category.objects.count()

    users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()

    # Category chart
    categories = Category.objects.annotate(place_count=Count("places"))

    labels = [c.title for c in categories]
    values = [c.place_count for c in categories]

    # Places growth
    places_growth = (
        LocalPlace.objects.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    growth_labels = [str(i["date"]) for i in places_growth]
    growth_values = [i["count"] for i in places_growth]

    # User registration growth (last 30 days)
    from datetime import timedelta

    thirty_days_ago = timezone.now() - timedelta(days=30)
    user_growth = (
        User.objects.filter(date_joined__gte=thirty_days_ago)
        .annotate(date=TruncDate("date_joined"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )
    user_growth_labels = [str(i["date"]) for i in user_growth]
    user_growth_values = [i["count"] for i in user_growth]

    context.update(
        {
            "stats": [
                {
                    "title": "Total Users",
                    "value": total_users,
                    "icon": "person",
                },
                {
                    "title": "Local Places",
                    "value": total_places,
                    "icon": "map",
                },
                {
                    "title": "Categories",
                    "value": total_categories,
                    "icon": "category",
                },
                {
                    "title": "Users Today",
                    "value": users_today,
                    "icon": "person_add",
                },
            ],
            "charts": [
                {
                    "title": "Places Per Category",
                    "type": "bar",
                    "data": {
                        "labels": mark_safe(json.dumps(labels)),
                        "datasets": [
                            {
                                "label": "Places",
                                "data": mark_safe(json.dumps(values)),
                                "backgroundColor": "#7c3aed",
                            }
                        ],
                    },
                },
                {
                    "title": "Places Growth Over Time",
                    "type": "line",
                    "data": {
                        "labels": mark_safe(json.dumps(growth_labels)),
                        "datasets": [
                            {
                                "label": "Places",
                                "data": mark_safe(json.dumps(growth_values)),
                                "borderColor": "#22c55e",
                            }
                        ],
                    },
                },
                {
                    "title": "User Registrations (Last 30 Days)",
                    "type": "line",
                    "data": {
                        "labels": mark_safe(json.dumps(user_growth_labels)),
                        "datasets": [
                            {
                                "label": "New Users",
                                "data": mark_safe(json.dumps(user_growth_values)),
                                "borderColor": "#6366f1",
                            }
                        ],
                    },
                },
            ],
            "latest_users": User.objects.order_by("-date_joined")[:5],
            "latest_places": LocalPlace.objects.order_by("-created_at")[:5],
        }
    )

    return context
