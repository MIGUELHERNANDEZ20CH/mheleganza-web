import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('app_productos', '0003_producto_imagen_url'),
        ('app_inventario', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MovimientoInventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('ENTRADA', 'Entrada'), ('SALIDA', 'Salida'), ('VENTA', 'Venta')], max_length=10)),
                ('cantidad', models.PositiveIntegerField()),
                ('stock_resultante', models.PositiveIntegerField()),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_inventario', to='app_productos.producto')),
            ],
            options={'ordering': ['-creado_en']},
        ),
        migrations.CreateModel(
            name='NotificacionInventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mensaje', models.CharField(max_length=200)),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('leida', models.BooleanField(default=False)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones_inventario', to='app_productos.producto')),
            ],
            options={'ordering': ['-creada_en']},
        ),
    ]