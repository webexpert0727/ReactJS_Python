#run migrate first before running this script!

from django.contrib.auth.models import Group, Permission
from customauth.models import MyUser

adminuser = MyUser.objects.get(email='admin@hookcoffee.com.sg')

packer = MyUser(email='packer@hookcoffee.com.sg')
packer.set_password('IONaphYMEnti')
packer.save()

p_group = Group(name="packer")
p_group.save()
packer.groups.add(p_group)
packer.save()

group = Group(name="admin")
group.save()
adminuser.groups.add(group)
adminuser.save()

permission = Permission.objects.get(codename='can_view_pack')
p_group.permissions.add(permission)
group.permissions.add(permission)
p_group.save()
group.save()

permission = Permission.objects.get(codename='can_view_customers')
p_group.permissions.add(permission)
group.permissions.add(permission)
p_group.save()
group.save()

permission = Permission.objects.get(codename='can_view_inventory')
p_group.permissions.add(permission)
group.permissions.add(permission)
group.save()
p_group.save()

permission = Permission.objects.get(codename='can_view_marketing')
group.permissions.add(permission)
group.save()

permission = Permission.objects.get(codename='can_view_analysis')
group.permissions.add(permission)
group.save()