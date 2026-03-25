from django.db import migrations

def add_cart_map_data(apps, schema_editor):
    CartMap = apps.get_model('local_places', 'CartMap')
    
    zones_data = [
        ("Zone 1", "Highway 80/Butler Avenue at locations south of Park of 7 Flags"),
        ("Zone 2", "At the traffic-controlled intersection of 14th Street and Highway 80"),
        ("Zone 3", "At the traffic-controlled intersection of Campbell Avenue and Highway 80"),
        ("Zone 4", "At the traffic-controlled intersection of Jones Avenue and Highway 80"),
    ]
    
    for title, desc in zones_data:
        CartMap.objects.update_or_create(
            title=title,
            defaults={'description': desc}
        )
    
    CartMap.objects.update_or_create(
        title="Whole Tybee Island",
        defaults={
            'description': "Golf carts may not drive on Highway 80 but may cross at these locations:",
            'map_file_type': 'image'
        }
    )

def remove_cart_map_data(apps, schema_editor):
    CartMap = apps.get_model('local_places', 'CartMap')
    titles = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Whole Tybee Island"]
    CartMap.objects.filter(title__in=titles).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('local_places', '0025_cartmap_map_file_type'),
    ]

    operations = [
        migrations.RunPython(add_cart_map_data, reverse_code=remove_cart_map_data),
    ]
