from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from django.utils.html import strip_tags

from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField


class Category(models.Model):
    name = models.CharField(_('Category'), max_length=32)
    slug = models.SlugField(unique=True, blank=True, help_text='Defined automatically')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(_('Tag'), max_length=32)
    slug = models.SlugField(unique=True, blank=True, help_text='Defined automatically')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Tag, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(_('Title'), max_length=128)
    preview = models.CharField(_('Preview'), max_length=512, blank=True)
    # content = models.TextField(_('Content'), max_length=5120)
    content = RichTextUploadingField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_published = models.DateTimeField(blank=True)
    author = models.CharField(_('Author'), max_length=32, default='Hook Coffee')
    img = models.ImageField(blank=True)

    category = models.ForeignKey(Category, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    slug = models.SlugField(
        unique=True,
        blank=True,
        max_length=128,
        help_text='Defined automatically but feel free to modify if needed'
    )

    def save(self, *args, **kwargs):
        if not self.date_published:
            self.date_published = timezone.now()
        if not self.preview:
            self.preview = strip_tags(self.content)[:256] + '..'
        if not self.slug:
            self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    def image_tag(self):
        return u'<img src="%s" width="480px" />' % self.img.url
    image_tag.short_description = 'Main image'
    image_tag.allow_tags = True

    def __unicode__(self):
        return self.title
