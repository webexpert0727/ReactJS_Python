from django.contrib import admin
from django import forms

from modeltranslation.admin import (
    TranslationStackedInline, TabbedDjangoJqueryTranslationAdmin)

from django.utils.dateparse import parse_datetime
from django.utils.safestring import mark_safe

from .models import *


@admin.register(Section)
class SectionTypeAdmin(TabbedDjangoJqueryTranslationAdmin):
    pass



@admin.register(Post)
class PostTypeAdmin(TabbedDjangoJqueryTranslationAdmin):

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name.startswith('message_'):
            kwargs['widget'] = forms.Textarea()
        return super(PostTypeAdmin, self).formfield_for_dbfield(db_field, **kwargs)


@admin.register(Review)
class ReviewTypeAdmin(TabbedDjangoJqueryTranslationAdmin):
    list_display = ('author', 'is_workplace',)


@admin.register(Career)
class CareerTypeAdmin(TabbedDjangoJqueryTranslationAdmin):
    pass


class BrewGuideStepInline(TranslationStackedInline):
    model = BrewGuideStep
    extra = 1


# @admin.register(News)
# class NewsAdmin(admin.ModelAdmin):
#     list_display = ('content', 'active')
#     list_filter = ('active',)
#     verbose_name_plural = 'new'


@admin.register(BrewGuide)
class BrewGuideAdmin(TabbedDjangoJqueryTranslationAdmin):
    # list_display = ('name', 'description', 'video', 'img', )
    inlines = (BrewGuideStepInline, )
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Greeting)
class GreetingAdmin(TabbedDjangoJqueryTranslationAdmin):
    pass


@admin.register(InstagramPost)
class InstagramPostAdmin(admin.ModelAdmin):
    list_display = ('image', 'author', 'text', 'url', 'created')

    def image(self, obj):
        return mark_safe('<img src="%s" width="200"/>' % obj.data['image_url'])
    image.short_description = 'Image'

    def author(self, obj):
        return obj.data['author_name']
    author.short_description = 'Author'

    def text(self, obj):
        return obj.data['text']
    text.short_description = 'Text'

    def created(self, obj):
        return parse_datetime(obj.data['created_time'])
    created.short_description = 'Created'


admin.site.register(TopBar)
