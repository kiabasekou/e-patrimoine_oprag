# Generated manually to fix Commune-Departement relationship
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('patrimoine', '0006_alter_commune_departement'),
    ]

    operations = [
        # Assure que tous les champs nécessaires sont correctement définis
        migrations.AlterField(
            model_name='commune',
            name='departement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patrimoine.departement'),
        ),
        # Vérifie l'existence des champs latitude et longitude
        migrations.AlterField(
            model_name='commune',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='commune',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]