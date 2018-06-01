from django.conf.urls import url
from blog.views import *


urlpatterns = [
    url(r'^$', index, name='blog'),
    url(r'^(?P<slug>[\w\d-]+)$', get_post, name='get-post'),
    # url(r'^posts/(?P<cat_slug>[\w\d-]+)?/(?P<tag>[\w\d-]+)?$', filter_posts, name='filter-posts-by-cat'),
    url(r'^category/(?P<cat_slug>.+)?/$', filter_posts, name='filter-posts-by-cat'),
    url(r'^tags/(?P<tag_slug>.+)?/$', filter_posts, name='filter-posts-by-tag'),
]
