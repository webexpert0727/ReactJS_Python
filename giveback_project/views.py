# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import urllib2

from jsonview.decorators import json_view

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.shortcuts import redirect, render

from content.models import Greeting, Review, InstagramPost

from customers.forms import GS_CustomerForm
from customers.models import Customer

from giveback_project.helpers import geo_check


logger = logging.getLogger(__name__)
MAX_LABELS_IN_FILE = settings.MAX_LABELS_IN_FILE
CACHE_EXPIRING_TIME = 60*60*24*3


@geo_check
def index(request, is_worldwide=None):
    context = {}
    reviews = Review.objects.filter(is_workplace=False)
    popup_ids = ['2']

    try:
        username = Customer.objects.get(user=request.user).first_name
    except Exception:
        username = ''

    greetings = prepare_greetings(username)

    # if is_worldwide is not None:
    #     context['is_worldwide'] = is_worldwide
    # else:
    #     context['choose_country'] = True

    # Used to show country list
    # cf = GS_CustomerForm(initial={'country': 'AF'})
    cf = GS_CustomerForm()

    context.update({
        'reviews': reviews,
        'popup_ids': popup_ids,
        'greetings': greetings,
        'instagram_posts': InstagramPost.objects.all(),
        'cf': cf,
        'current_domain': Site.objects.get_current().domain,
    })
    return render(request, 'giveback_project/index.html', context)


def choose_country(request):
    # If value is 0, the user’s session cookie will expire when the user’s Web browser is closed
    request.session.set_expiry(0)
    request.session['is_worldwide'] = request.POST.get('is_global', False)

    return redirect('index')


def prepare_greetings(username):
    morning = Greeting.objects.get(time_of_day='morning')
    morning_line1 = morning.line1.format(username=username)
    morning_line2 = morning.line2.format(username=username)
    morning_line3 = morning.line3.format(username=username)

    noon = Greeting.objects.get(time_of_day='noon')
    noon_line1 = noon.line1.format(username=username)
    noon_line2 = noon.line2.format(username=username)
    noon_line3 = noon.line3.format(username=username)

    evening = Greeting.objects.get(time_of_day='evening')
    evening_line1 = evening.line1.format(username=username)
    evening_line2 = evening.line2.format(username=username)
    evening_line3 = evening.line3.format(username=username)

    return {
        'morning': [morning_line1, morning_line2, morning_line3],
        'noon': [noon_line1, noon_line2, noon_line3],
        'evening': [evening_line1, evening_line2, evening_line3],
    }


@json_view
def social_data(request):
    def _fetch_data(url):
        try:
            resp = urllib2.urlopen(url)
            data = json.loads(resp.read())
            resp.close()
        except Exception:
            logger.error('Fetch social data. url: %s', url, exc_info=True)
            data = {}
        return data

    fb_url = 'https://graph.facebook.com/'
    page_id = settings.FB_PAGE_ID
    token = settings.FB_PAGE_ACCESS_TOKEN

    insta_url = 'https://www.instagram.com/hook_coffee/media/'

    ratings_query = '%(page)s%(q)s&access_token=%(token)s'
    overall_url = fb_url + ratings_query % {
        'page': page_id,
        'q': '?fields=overall_star_rating,rating_count',
        'token': token}
    reviews_url = fb_url + ratings_query % {
        'page': page_id, 'q': '/ratings?limit=15', 'token': token}

    fb_overall = cache.get('fb_overall', {})
    if not fb_overall:
        fb_overall = _fetch_data(overall_url)
        if fb_overall.get('id'):  # to be sure we got correct response
            cache.set('fb_overall', fb_overall, CACHE_EXPIRING_TIME)

    fb_reviews = cache.get('fb_reviews', [])
    if not fb_reviews:
        raw_fb_reviews = _fetch_data(reviews_url)
        for review in (raw_fb_reviews.get('data') or []):
            if review.get('rating') < 4:  # haters gona hate
                continue
            reviewer_id = review['reviewer']['id']
            reviewer_url = fb_url + '%s/picture?type=square&redirect=0' % reviewer_id
            reviewer_resp = _fetch_data(reviewer_url)
            reviewer_data = reviewer_resp.get('data')
            if reviewer_data:
                review['img'] = reviewer_data.get('url')
            if review.get('review_text') and review.get('img'):
                # skip reviews without comment and photo
                fb_reviews.append(review)
        if fb_reviews:
            cache.set('fb_reviews', fb_reviews, CACHE_EXPIRING_TIME)

    # insta_posts = cache.get('insta_posts', [])
    # if not insta_posts:
    #     resp = _fetch_data(insta_url)
    #     for item in (resp.get('items') or [])[:3]:
    #         insta_posts.append({
    #             'full_name': item['user']['full_name'],
    #             'profile_img': item['user']['profile_picture'],
    #             'created_time': item['created_time'],
    #             'text': item['caption']['text'],
    #             # 'location': item['location']['name'],
    #             # 'link': item['link'],
    #             'img': item['images']['low_resolution']['url'],
    #         })
    #     if insta_posts:
    #         cache.set('insta_posts', insta_posts, None)

    return {'fb_overall': fb_overall, 'fb_reviews': fb_reviews}
