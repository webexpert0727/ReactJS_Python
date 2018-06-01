################################################################
# remove image captions and other garbage from migration       #
################################################################

import re
from blog.models import Post


pattern = re.compile(r'\[caption.+(<img.+\/>).*\[\/caption\]')


def cap_repl(matchobj):
    print 'FOUND:', matchobj.group(0)
    print 'EXTRACTED:', matchobj.group(1)
    return matchobj.group(1)


def main():
    posts = Post.objects.all()
    for post in posts:
        print 'post id:', post.id
        post.content = re.sub(pattern, cap_repl, post.content)
        post.save()


if __name__ == '__main__':
    main()
