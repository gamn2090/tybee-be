from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("local_places", "0026_add_whole_tybee_map"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="localplaceimage",
            unique_together=set(),
        ),
    ]
