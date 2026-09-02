from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenancy', '0016_tenant_setup_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='email',
            field=models.EmailField(blank=True, help_text='Shop email address for documents', max_length=254, null=True),
        ),
    ]
