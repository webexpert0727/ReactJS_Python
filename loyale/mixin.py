# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from customers.models import Customer

from giveback_project.helpers import get_shipping_date

from .models import (Point,
                     RedemItem,
                     RedemPointLog,
                     GrantPointLog,
                     CoffeeTypePoints)


POINTS_FOR_INVITED_FRIEND = 20
POINTS_FOR_EXP_SURVEY = 200


class PointMixin(object):

    def is_subscribe(self, user):
        """Check if customer is subscribe
        """
        try:
            Customer.objects.get(user=user)
            return True
        except Customer.DoesNotExist:
            return False

    def coffee_points(self, user, coffee):
        """Add points base on coffee
        """
        if self.is_subscribe(user):
            try:
                points = CoffeeTypePoints.objects.get(coffee_type=coffee, status='subscribe').points
            except CoffeeTypePoints.DoesNotExist:
                points = 0
        else:
            try:
                points = CoffeeTypePoints.objects.get(coffee_type=coffee, status='none').points
            except CoffeeTypePoints.DoesNotExist:
                points = 0

        self.grant_points(user, points)


    def grant_points(self, user, points):
        """Add points to user
        """
        try:
            point = Point.objects.get(user=user)
            point.points += points
            point.save()
        except Point.DoesNotExist:
            point = Point(user=user, points=points)
            point.save()

        GrantPointLog.objects.create(points=points, user=user)
        return point.points

    def redemed_points(self, user):
        """Get the total redemed points
        """
        redems = RedemPointLog.objects.filter(user=user)
        points = 0

        for instance in redems:
            points += instance.points

        return points

    def accumulated_points(self, user):
        """Get consumed points
        """
        logs = GrantPointLog.objects.filter(user=user)
        points = 0

        for instance in logs:
            points += instance.points

        return points

    def ralphs_redem_item(self, user, item):
        """Redem item by points
        """
        redemed_points = 0
        user_point = Point.objects.get(user=user)
        points = user_point.points
        print 'User has had ', points, ' points'

        if points:
            redem_item, create = RedemItem.objects.get_or_create(user=user, item=item, status='pending')
            print 'Redeem item is ', redem_item.item

            if create:
                # if redem item created set redem item points
                redem_item.points = item.points
                print "Redeem item created, ", redem_item.points, ' points'

            # deduct the points based on redem item
            if points >= item.points:
                user_point.points = points - redem_item.points
            else:
                user_point.points = 0

            if redem_item.points >= points:
                redem_item.points = redem_item.points - points
                redemed_points = redem_item.points
            else:
                redemed_points = item.points
                redem_item.points = 0

            # if points is 0 set status to done
            if redem_item.points == 0:
                redem_item.status = 'done'
                message = """You have successfully redemed an item.

                Item: {}
                Points: {}
                """.format(redem_item.item.name, item.points)
                # send_mail('You Redemed an Item', message, settings.DEFAULT_FROM_EMAIL,
                        # [user.email, ], fail_silently=False)

                print 'Summary message: ', message

            redem_item.save()
            user_point.save()

            RedemPointLog.objects.create(user=user, item=item, points=redemed_points)

            return redem_item

        return None

    def redem_item(self, user, item):
        """Redem item"""

        point = Point.objects.get(user=user)
        print 'User has had ', point.points, ' points'

        redem_item = RedemItem(user=user, item=item, points=item.points, shipping_date=get_shipping_date())
        redem_item.save()
        print 'Redeem item is ', redem_item.item

        point.points -= item.points
        point.save()

        RedemPointLog.objects.create(user=user, item=item, points=redem_item.points)

        return redem_item
