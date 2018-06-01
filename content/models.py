# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import re
import urllib2

from django_hstore import hstore

from django.core.urlresolvers import reverse
from django.db import models


logger = logging.getLogger('giveback_project.' + __name__)


class Section(models.Model):
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return '{}'.format(self.name)


class Post(models.Model):
    section = models.ForeignKey(Section)
    title = models.CharField(max_length=128)
    message = models.CharField(max_length=1536)

    def __unicode__(self):
        return '{} | {}'.format(self.section, self.title)


class Review(models.Model):
    author = models.CharField(max_length=128)
    message = models.CharField(max_length=1536)
    is_workplace = models.BooleanField(default=False)
    logo = models.ImageField(blank=True, null=True)

    def __unicode__(self):
        return self.author


class Career(models.Model):
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=1024)
    active = models.BooleanField(default=True)
    img = models.ImageField(blank=True)

    def __unicode__(self):
        return self.title


# class News(models.Model):
#     content = models.CharField("Header text", max_length=256)
#     active = models.BooleanField('Is active', default=True)

#     def __unicode__(self):
#         return self.content


class BrewGuide(models.Model):
    name = models.CharField(max_length=20)
    subtitle = models.CharField(max_length=20, blank=True)
    slug = models.SlugField(unique=True, max_length=20)
    description = models.TextField()
    video = models.CharField(max_length=20)
    required_list = models.TextField()
    brew_time = models.CharField(max_length=50, default='30 seconds')
    img = models.ImageField()
    banner = models.ImageField()
    banner_txt_bcolor = models.CharField(
        max_length=7,
        default='#eeeeee',
        help_text='Background color (in HEX format) for left part')
    banner_img_bcolor = models.CharField(
        max_length=7,
        default='#eeeeee',
        help_text='Background color (in HEX format) for right part')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('brew_guide_details', kwargs={'slug': self.slug})


class BrewGuideStep(models.Model):
    brew_guide = models.ForeignKey(BrewGuide, related_name='steps')
    img = models.ImageField(blank=True, null=True)
    description = models.TextField()

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return str(self.pk)


class Greeting(models.Model):
    time_of_day = models.CharField(max_length=16)
    line1 = models.CharField(max_length=128)
    line2 = models.CharField(blank=True, max_length=256)
    line3 = models.CharField(max_length=512)

    def __unicode__(self):
        return self.time_of_day


class InstagramPost(models.Model):
    url = models.URLField(max_length=256)
    data = hstore.SerializedDictionaryField(blank=True, editable=False)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.data = self.fetch_post_data()
            print 'self.data:::', self.data
            if not self.data:
                raise ValueError('Cannot be saved, try again or '
                                 'ask your developer to check it out')
        super(InstagramPost, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.url

    def fetch_post_data(self):
        resp = self._fetch_data(
            'https://api.instagram.com/oembed/?url=%s' % self.url)
        if not resp:
            raise ValueError('Cannot get the post data, try again later')
        author_name = resp['author_name']
        caption = resp.get('title')
        return {
            'author_name': author_name,
            'author_avatar': self._fetch_author_avatar(author_name),
            'author_url': resp['author_url'],
            'image_url': self._get_image_url(author_name, caption),
            'text': resp['title'],
            'created_time': re.findall(r'datetime=\"([\dT:+-]+)\"', resp['html'])[0],
        }

    def _fetch_author_avatar(self, username):
        author_media = self._fetch_data("https://www.instagram.com/{username}/?__a=1".format(username=username))
        avatar_url = "https://instagramstatic-a.akamaihd.net/null.jpg"
        if author_media:
            avatar_url = author_media['user']['profile_pic_url']

        return avatar_url

    def _get_image_url(self, username, caption):
        author_media = self._fetch_data("https://www.instagram.com/{username}/?__a=1".format(username=username))
        image_url = "https://instagramstatic-a.akamaihd.net/null.jpg"
        if author_media:
            for node in author_media['user']['media']['nodes']:
                if node.get('caption') == caption:
                    image_url = node['thumbnail_src']
                    break
        return image_url

    def _fetch_data(self, url):
        try:
            resp = urllib2.urlopen(url)
            data = json.loads(resp.read())
            resp.close()
        except Exception:
            logger.error('Fetch social data. url: %s', url, exc_info=True)
            data = {}
        return data


class TopBar(models.Model):
    block_text = models.CharField(max_length=256)
    button_text = models.CharField(
        max_length=36, blank=True,
        help_text=('Leave this field blank if you want to make '
                   'the text clickable (the text will be a link)'))
    link = models.URLField(max_length=256)
    visible = models.BooleanField(default=False)
