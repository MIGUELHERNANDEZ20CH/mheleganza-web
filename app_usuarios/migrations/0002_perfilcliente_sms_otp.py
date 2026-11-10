from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilcliente',
            name='sms_code',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='perfilcliente',
            name='code_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='perfilcliente',
            name='sms_code_attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
