from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_pedido', '0002_detallepedido_talla'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='stripe_checkout_session_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='pedido',
            name='stripe_payment_intent_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='pedido',
            name='confirmacion_email_enviada',
            field=models.BooleanField(default=False),
        ),
    ]
