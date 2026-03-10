import django.db.models.deletion
from django.db import migrations, models


def migrate_categories_forward(apps, schema_editor):
    """
    Create RuleCategory objects from existing string category values,
    then link each Rule to the corresponding RuleCategory.
    """
    Rule = apps.get_model("rules", "Rule")
    RuleCategory = apps.get_model("rules", "RuleCategory")

    # Map old string choices to human-readable names and slugs
    category_map = {
        "golf_cart": ("Golf Cart", "golf_cart"),
        "bicycle": ("Bicycle", "bicycle"),
    }

    # Ensure categories exist for every unique value in existing rules
    existing_values = Rule.objects.values_list("old_category", flat=True).distinct()
    for value in existing_values:
        if value in category_map:
            name, slug = category_map[value]
        else:
            name = value.replace("_", " ").title()
            slug = value
        cat, _ = RuleCategory.objects.get_or_create(slug=slug, defaults={"name": name})

    # Link each Rule to its new category FK
    for rule in Rule.objects.all():
        value = rule.old_category
        if value in category_map:
            _, slug = category_map[value]
        else:
            slug = value
        cat = RuleCategory.objects.get(slug=slug)
        rule.category = cat
        rule.save()


def migrate_categories_backward(apps, schema_editor):
    Rule = apps.get_model("rules", "Rule")
    for rule in Rule.objects.select_related("category").all():
        rule.old_category = rule.category.slug
        rule.save()


class Migration(migrations.Migration):

    dependencies = [
        ("rules", "0001_initial"),
    ]

    operations = [
        # 1. Create the RuleCategory table
        migrations.CreateModel(
            name="RuleCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=100, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Rule Category",
                "verbose_name_plural": "Rule Categories",
                "ordering": ["name"],
            },
        ),
        # 2. Rename old category CharField to old_category so we can keep the data
        migrations.RenameField(
            model_name="rule",
            old_name="category",
            new_name="old_category",
        ),
        # 3. Add the new nullable FK column
        migrations.AddField(
            model_name="rule",
            name="category",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="rules",
                to="rules.rulecategory",
            ),
        ),
        # 4. Run data migration: create RuleCategory rows and link rules
        migrations.RunPython(migrate_categories_forward, migrate_categories_backward),
        # 5. Remove the old string column
        migrations.RemoveField(
            model_name="rule",
            name="old_category",
        ),
        # 6. Make the FK non-nullable now that all rows are filled
        migrations.AlterField(
            model_name="rule",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="rules",
                to="rules.rulecategory",
            ),
        ),
    ]
