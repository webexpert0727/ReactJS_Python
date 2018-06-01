from lxml import etree
from dateutil import parser
from blog.models import Category, Tag, Post


tree = etree.parse('blog/blog.xml')
root = tree.getroot()


def main():

    categories = set()
    tags = set()
    posts = []

    for item in root.find('channel').findall('item'):
        if item.find('wp:status', root.nsmap).text == 'publish':
            category = get_category(item)
            category, created = Category.objects.get_or_create(slug=category[0], name=category[1])

            tags_raw = get_tags(item)
            tags = set()
            for x in tags_raw:
                tag, created = Tag.objects.get_or_create(slug=x[0], name=x[1])
                tags.add(tag)

            post, created = Post.objects.get_or_create(
                title=get_title(item),
                # preview=,
                content=get_content(item),
                # date_added=,
                date_published=get_date(item),
                author=get_author(item),
                # img=,
                category=category,
                # tags=,
                slug=get_slug(item),
            )

            for x in tags:
                post.tags.add(x)


def get_element_name(e):
    return e.text or 'Uncategorized'


def get_element_slug(e):
    return e.get('nicename') or 'uncategorized'


def get_category(e):
    for i in e.findall('category'):
        if i.get('domain') == 'category':
            return (get_element_slug(i), get_element_name(i))

    return ('uncategorized', 'Uncategorized')


def get_tags(e):
    tags = []
    for i in e.findall('category'):
        if i.get('domain') == 'post_tag':
            tags.append((get_element_slug(i), get_element_name(i)))

    return tags


def get_title(e):
    return e.find("title").text


def get_slug(e):
    return e.find('wp:post_name', root.nsmap).text


def get_content(e):
    return e.find('content:encoded', root.nsmap).text


def get_date(e):
    return parser.parse(
        e.find('pubDate').text
        )


def get_author(e):
    return e.find('dc:creator', root.nsmap).text


if __name__ == '__main__':
    main()
