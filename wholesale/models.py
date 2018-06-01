from adminsortable.models import SortableMixin

from django.db import models


TYPE_1 = 'W'
TYPE_2 = 'WO'

OFFICE_TYPES = (
    (TYPE_1, 'Offices with a coffee machine'),
    (TYPE_2, 'Offices without a coffee machine'),
)


class Plan(SortableMixin):
    name = models.CharField("Title", max_length=64)

    office_type = models.CharField(max_length=48, choices=OFFICE_TYPES, blank=True, null=True, default=TYPE_2)

    goal_1 = models.CharField("Goal 1", max_length=128)
    goal_2 = models.CharField("Goal 2", max_length=128, blank=True, null=True)
    goal_2_note = models.CharField("Goal 2 note", max_length=128,\
        blank=True, null=True, default=None)

    description_1 = models.CharField("Description 1", max_length=128)
    description_2 = models.CharField("Description 2", max_length=128, blank=True, null=True)
    description_2_note = models.CharField("Description 2 note", max_length=128,\
        blank=True, null=True, default=None)

    comments = models.CharField("Comments", max_length=256)

    price = models.DecimalField('Price', max_digits=6, decimal_places=2,\
        blank=True, null=True, default=None)
    img = models.ImageField()

    the_order = models.PositiveIntegerField(default=0, editable=False)


    class Meta:
        ordering = ('the_order',)

    def __unicode__(self):
        return self.name
