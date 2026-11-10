from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfilCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telefono', models.CharField(max_length=20, unique=True)),
                ('direccion', models.TextField(blank=True)),
                ('rol', models.CharField(choices=[('cliente', 'Cliente'), ('admin', 'Administrador')], default='cliente', max_length=10)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_cliente', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]