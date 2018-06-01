# -*- coding: utf-8 -*-

from modeltranslation.translator import register, TranslationOptions
from content.models import Section, Post, Review,\
    Career, BrewGuide, BrewGuideStep, Greeting


@register(Section)
class SectionTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ('title', 'message')


@register(Review)
class ReviewTranslationOptions(TranslationOptions):
    fields = ('author', 'message')


@register(Career)
class CareerTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(BrewGuide)
class BrewGuideTranslationOptions(TranslationOptions):
    fields = ('name', 'subtitle', 'description', 'required_list', 'brew_time', )


@register(BrewGuideStep)
class BrewGuideStepTranslationOptions(TranslationOptions):
    fields = ('description', )


@register(Greeting)
class GreetingTranslationOptions(TranslationOptions):
    fields = ('line1', 'line2', 'line3',)
