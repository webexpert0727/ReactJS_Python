# -*- coding: utf-8 -*-

from modeltranslation.translator import register, TranslationOptions
from wholesale.models import Plan


@register(Plan)
class PlanTranslationOptions(TranslationOptions):
    fields = ('name', 'goal_1', 'goal_2', 'goal_2_note', 'description_1',
              'description_2', 'description_2_note', 'comments')
