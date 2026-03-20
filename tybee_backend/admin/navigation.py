from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

NAVIGATION = [
    {
        "title": _("Users"),
        "separator": True,
        "items": [
            {
                "title": _("Users"),
                "icon": "person",
                "link": reverse_lazy("admin:users_user_changelist"),
            },
            # Password Reset OTPs hidden as requested
            # {
            #     "title": _("Password Reset OTPs"),
            #     "icon": "lock_reset",
            #     "link": reverse_lazy("admin:users_passwordresetotp_changelist"),
            # },
        ],
    },
    {
        "title": _("Places"),
        "separator": True,
        "items": [
            {
                "title": _("Local Places"),
                "icon": "map",
                "link": reverse_lazy("admin:local_places_localplace_changelist"),
            },
            {
                "title": _("Restaurants"),
                "icon": "restaurant",
                "link": reverse_lazy("admin:local_places_restaurant_changelist"),
            },
            {
                "title": _("Categories"),
                "icon": "category",
                "link": reverse_lazy("admin:local_places_category_changelist"),
            },
            {
                "title": _("Tags"),
                "icon": "label",
                "link": reverse_lazy("admin:local_places_tag_changelist"),
            },
            {
                "title": _("Activities"),
                "icon": "directions_run",
                "link": reverse_lazy("admin:local_places_activity_changelist"),
            },
            {
                "title": _("Live Like a Local"),
                "icon": "tips_and_updates",
                "link": reverse_lazy("admin:local_places_livelikealocal_changelist"),
            },
            {
                "title": _("Cart Maps"),
                "icon": "map",
                "link": reverse_lazy("admin:local_places_cartmap_changelist"),
            },
        ],
    },
    {
        "title": _("Rules"),
        "separator": True,
        "items": [
            {
                "title": _("Rule Categories"),
                "icon": "folder",
                "link": reverse_lazy("admin:rules_rulecategory_changelist"),
            },
            {
                "title": _("Rules"),
                "icon": "gavel",
                "link": reverse_lazy("admin:rules_rule_changelist"),
            },
        ],
    },
    {
        "title": _("Legal"),
        "separator": True,
        "items": [
            {
                "title": _("Legal Documents"),
                "icon": "description",
                "link": reverse_lazy("admin:legal_legaldocument_changelist"),
            },
        ],
    },
    {
        "title": _("Feedback"),
        "separator": True,
        "items": [
            {
                "title": _("User Feedback"),
                "icon": "feedback",
                "link": reverse_lazy("admin:feedback_userfeedback_changelist"),
            },
            {
                "title": _("Help Requests"),
                "icon": "help",
                "link": reverse_lazy("admin:feedback_helprequest_changelist"),
            },
            {
                "title": _("Report Problems"),
                "icon": "report",
                "link": reverse_lazy("admin:feedback_reportproblem_changelist"),
            },
            {
                "title": _("Contact Us"),
                "icon": "mail",
                "link": reverse_lazy("admin:feedback_contactus_changelist"),
            },
        ],
    },
]
