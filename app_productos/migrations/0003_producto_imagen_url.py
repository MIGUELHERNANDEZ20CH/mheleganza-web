from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('app_productos', '0002_remove_producto_stock_producto_disponible_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='imagen_url',
            field=models.URLField(blank=True),
        ),
    ]