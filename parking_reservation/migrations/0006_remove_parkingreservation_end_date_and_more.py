# Generated by Django 5.1.5 on 2025-06-21 11:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parking_reservation', '0005_parkingfeemodel'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parkingreservation',
            name='end_date',
        ),
        migrations.RemoveField(
            model_name='parkingreservation',
            name='start_date',
        ),
    ]
