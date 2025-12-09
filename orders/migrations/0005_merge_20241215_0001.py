from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_add_product_snapshot_fields"),
        ("orders", "0004_add_index_to_status_fields"),
    ]

    operations = []
