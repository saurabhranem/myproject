from django.contrib.auth.models import User, Group, Permission
from django.core.management.base import BaseCommand

from app.models import Brand, UserBrand


class Command(BaseCommand):
    help = 'Loads initial user and group to database'

    def handle(self, *args, **options):
        permission = Permission.objects.all().exclude(name__contains='delete')
        group = Group.objects.create(name='Admin')
        group.permissions = permission
        group.save()
        print "Admin Group created"
        user = User.objects.create(username='SuperAdmin')
        user.set_password('Gladminds@123')
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print "Super User Created"
        user_admin = User.objects.create(username='Admin')
        user_admin.set_password('Gladminds@123')
        user_admin.is_active = True
        user_admin.is_staff = True
        user_admin.save()
        print("Users and Groups  are created")
        group_machine = Group.objects.create(name='SuperVisor')
        print "Supervisor Group created"
        # group_machine = Group.objects.create(name='ReadOnly')
        # print "ReadOnly Group created"
        group_superadmin = Group.objects.create(name='SuperAdmin')
        print "SuperAdmin Group created"
        group_plant = Group.objects.create(name='PlantAdmin')
        print "PlantAdmin Group created"
        brand = Brand.objects.create(name='Shakti')
        print "Brand is created"
        brand_user = UserBrand.objects.create(
            user=user, brand=brand, group=group_superadmin, mobile_number="9965615321"
        )
        print "superadmin permission is enabled"
        brand_user = UserBrand.objects.create(
            user=user_admin, brand=brand, group=group, mobile_number="8838319938"
        )
        print "Admin permission is enabled"

