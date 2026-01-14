# DailyPaper

Basic rss reader that displays comics and articles in columns.
Requires python.
To use run `python paperServer.py` (Included as a .bat file called **Run.bat**).
This will start a server that loads and parses all the rss feeds and turns them into a local website.
Navigate to the url shown in python script and there you go.

To add comics or articles put the info into **comics.json** with this format:

`
{
	"comic_feeds":[
		{"name":"Greatures", "rss":"https://greatures.com/comic/feed"},
		{"name":"Swan Boy", "rss":"https://www.swanboy.com/feed"}
	],
	"article_feeds":[
		{"name":"Josh Reads", "rss":"https://joshreads.com/feed/"},
		{"name":"Mike Rugnetta", "rss":"https://buttondown.com/mikerugnetta/rss"}
	]
}
`

If things aren't working it's probably because the rss feed is not formatted the way the program expects it to be.
Fixes for individual feeds can be made in **feedLoader.py** inside the **ComicsLoader.parseXML** or **PageLoader.parseXML** methods.

For example, the ComicsLoader class expects the xml to have a div containing an image, and it takes the source from that image.
The feed for Swan Boy is not formatted that way so it has to get the image source differently.

`
if len(src) == 0:
    # This is for Swan Boy specifically
    try:
        content = i.find('content')
        content = stringToHTML(content.text)
        src = content.xpath('//img/@data-large-file')
    except:
        src = []
`
