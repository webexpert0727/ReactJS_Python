# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import string
import random

from unidecode import unidecode

from customers.models import Customer, Referral

for cus in Customer.objects.all():
    flag = False
    try:
        flag = Referral.objects.get(user=cus.user)
    except:
        pass

    if not flag:
        print cus.user, 'CREATE!'
        new_ref = Referral(user=cus.user)
        first_name = '_'.join(unidecode(cus.first_name).split()).upper()
        code = '{}{}{}'.format(first_name, cus.user.id,
            ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)))
        new_ref.code = code
        new_ref.save()
    # else:
        # print cus.user, 'exists'
