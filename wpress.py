#! /usr/bin/python
# take stdin from teletype via ser.py and post to wordpress blog
# First nonblank line is the wordpress post title.
# everything after that is concatenated and sent verbatim.
# It will try to insert formatting to make the text look nice
# as a wordpress blog entry. 

import wordpresslib
import sys

# Fill in the wordpress blog URL, username, and password here:
url="http://MY_BLOG_URL/blog/xmlrpc.php"
username = 'MY_BLOG_USERNAME'
password = 'MY_BLOG_PASSWORD'

blob = sys.stdin.readlines()

i = 0
for line in blob:
    i = i + 1
    if line.isspace():
        print "ignoring line", i
    else:
	print "using line", i, "as title"
	title = line
	break

longest = 0
for line in blob[i:]:
    if len(line) > longest:
        longest = len(line)

print "longest line is", longest, "chars"

if longest <= 59:
    font = 14
elif longest <= 68:
    font = 12
else:
    font = 10

print "using font size %d px" % (font)

postbody = ''.join(blob[i:])
print "TITLE:", title

postbody = '<div style="font-family: monospace; font-size: %dpx;">' % (font) + postbody + '</div>'
print "BODY:", postbody

url="http://mumbleblog.vm.slothtown.com/blog/xmlrpc.php"
wp=wordpresslib.WordPressClient(url, username, password)
wp.selectBlog(0)
post=wordpresslib.WordPressPost()
post.title = title
post.description = postbody
post.tags = ['telegram']
idPost = wp.newPost(post, True)


