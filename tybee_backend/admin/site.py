from django.contrib.admin import AdminSite


class TybeeAdminSite(AdminSite):

    site_header = "Tybee Admin Dashboard"
    site_title = "Tybee Admin Dashboard"
    index_title = "Welcome to Tybee Admin Dashboard"


tybee_admin_site = TybeeAdminSite(name="tybee_admin")
