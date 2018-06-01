from django.contrib import admin

from blog.models import Category, Tag, Post
from blog.forms import PostForm

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    readonly_fields = ('slug',)
    list_display = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    readonly_fields = ('slug', )
    list_display = ('name', )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostForm
    readonly_fields = ('date_added', 'image_tag', )
    list_display = ('title', 'get_category', 'get_tags', 'date_published', )
    list_filter = ('tags', )
    search_fields = ('tag', )
    ordering = ('-date_published', )
    fields = ('title', 'author', 'date_published',
        'preview', 'content',
        'category', 'tags',
        'img', 'image_tag',)

    def get_tags(self, obj):
        return ', '.join([x.name for x in obj.tags.all()]) or '-'
    get_tags.short_description = 'Tags'

    def get_category(self, obj):
        return obj.category or '-'

