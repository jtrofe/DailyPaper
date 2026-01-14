import requests
from threading import Thread
import xml.etree.ElementTree as ET
from lxml.html import fromstring as stringToHTML
from dateutil.parser import parse as parseDate
import hashlib
from lxml_html_clean import Cleaner
import base64

HTML_CLEANER = Cleaner(style=True, scripts=True,javascript=True, add_nofollow=True,
                    safe_attrs_only=True)
HTML_CLEANER.safe_attrs = frozenset({'alt', 'class', 'cols', 'colspan', 'href', 'rows', 'rowspan', 'src'})

def removeStyle(html):
  style = re.compile(' style\=.*?\".*?\"')    
  html = re.sub(style, '', html)

  return(html)

__all__ = ['ComicsLoader', 'PageLoader']

def hashString(s):
    h = hashlib.new('sha256')
    h.update(s.encode())
    return h.hexdigest()

def dateToString(dt):
    return dt.strftime('%a %B %d, %Y')

def xmlDateToString(el, path):
    return dateToString(parseDate(el.find(path).text))

def createButton(id, text, on_click=None, disabled=False):
    if on_click:
        on_click = f'onclick="{on_click}" '
    else:
        on_click = ''
    disabled = 'disabled="" ' if disabled else ''
    
    return f'<button id="{id}" {disabled}{on_click}>{text}</button>'

class FeedLoader:
    '''
    Get the list of rss feeds with the type `type_name`
    and load the data from the rss urls
    '''
    def __init__(self, json_data, type_name):
        self.feeds = json_data[type_name]
        
        # Start the threads
        threads = []
        for i, f in enumerate(self.feeds):
            self.feeds[i]['id'] = hashString(f['name'])
            t = Thread(target=self.loadRSS, args=[f['rss'], i])
            t.start()
            threads.append(t)
        
        # Pause execution until they all finish
        for t in threads:
            t.join()
        
        # Parse the loaded XML into html
        for i, f in enumerate(self.feeds):
            if not 'success' in f:
                self.feeds[i]['html'] = f'<div>Error loading {f["name"]}</div>'
                continue
            if f['success']:
                f['parsedFeed'] = self.parseXML(f['feedXML'], f['id']) 
                feedHTML = self.feedToHTML(f)
                self.feeds[i]['html'] = feedHTML
                #del self.feeds[i]['feedXML'] # Do some cleanup
        
        # Make sure they all have html
        for f in self.feeds:
            if 'html' not in f:
                f['html'] = f'<div>Error loading {f["name"]}</div>'
    
    def __getitem__(self, i):
        return self.feeds[i]
    
    def __len__(self):
        return len(self.feeds)
    
    '''
    Threadable function which downloads an rss feed
    and stores the parsed XML object into the feed list
    '''
    def loadRSS(self, url, index):
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0'}, timeout=5)
        except Exception as e:
            self.feeds[index]['error'] = str(e)
            self.feeds[index]['success'] = False
            return
        
        if response.status_code != 200:
            f = self.feeds[index]
            self.feeds[index]['error'] = response.text
            self.feeds[index]['success'] = False
            return
        
        txt = response.text
        txt = txt.replace('content:encoded', 'content')
        self.feeds[index]['feedXML'] = ET.fromstring(txt)
        
        self.feeds[index]['success'] = True
    
    '''
    Turn the feed list of xml into an object structured something like this:
    {
        'name'      - feed's name
        'id'        - hashed feed name
        'buildDate' - last time the feed was updated
        'items'     - a list of all the items in this feed
    }
    
    item is a list of objects with (at least) these fields
    {
        'index'     - this object's index in the `items` list
        'date'      - this object's published date
        'link'      - link to the object
        'content'   - whatever the relevant info for this object is
    }
    
    The exact data included will depend on what the feed is for and
    parsing the specifics will be handled by a function that must
    be written for each type
    '''
    def parseXML(self, tree, id):
        raise NotImplementedError
    
    def feedToHTML(self, feed):
        raise NotImplementedError
    
    '''
    Convert the feed list into javascript code of this structure:
    
    globalThis.[type name] = {
            feed_0_id: {
                    name,
                    id,
                    buildDate,
                    items
                },
            
            feed_1_id: {
                },
            
                ...
        }
    '''
    def ToJavascript(self, var_name):
        feedHTML = []
        for f in self.feeds:
            if not 'success' in f or not f['success']: continue
            name = f['name']
            id = f['id']
            buildDate = f['parsedFeed']['buildDate']
            
            itemHTML = ','.join(self.itemToJavascript(i) for i in f['parsedFeed']['items'])
            
            feedHTML.append(
                    f'"{id}":{{"name":"{name}", "buildDate":"{buildDate}", "items":[{itemHTML}]}}'
                )
        feedHTML = ','.join(feedHTML)
        return f'globalThis.{var_name} = {{{feedHTML}}};'
    
    '''
    Extract info from the parsed XML and convert to javascript
    '''
    def itemToJavascript(self, item):
        raise NotImplementedError

class PageLoader(FeedLoader):
    def __init__(self, json_data):
        super().__init__(json_data, 'article_feeds')
    
    def parseXML(self, tree, id):
        buildDate = xmlDateToString(tree, './channel/lastBuildDate')
        
        articles = []
        items = tree.findall('./channel/item')
        feedTitle = tree.find('./channel/title').text
        for i in items:
            try:
                pubDate = xmlDateToString(i, 'pubDate')
            except:
                print(f'Unable to find pub date for {feedTitle}')
                continue
            link = i.find('link').text
            content = i.find('content')
            if content is None: content = i.find('description')
            content = content.text
            # Remove anything before the first <p> tag
            if feedTitle == 'The Comics Curmudgeon':
                content = content[content.index('<p>'):].strip()
            
            if feedTitle == 'LOW←TECH MAGAZINE English':
                # For some reason the </div> tags are all doubled in this feed
                content = content.replace('</div>\n</div>', '</div>')
            
            title = i.find('title').text
            
            # Remove styles and scripts
            try:
                content = HTML_CLEANER.clean_html(content)
            except Exception as e:
                print(f'Error cleaning html for "{feedTitle}":')
                print(f'Content: {content}')
                print(str(e))
                content = f'<div>Error cleaning html for "{feedTitle}"</div>'
            
            if "The latest local headlines from WHYY" in content:
                # These aren't articles it just says that and nothing else
                continue
            content = f'<div><a href="{link}">Permalink</a></div>{content}'
            
            closeButton = f'<button onclick="closeDetail(this.parentElement)">▲ Close article</button>'
            
            if len(content) > 10000:
                content = f'<details id="details_{id}"><summary>{title}</summary>{content}{closeButton}</details>'
            else:
                content = f'<details open id="details_{id}"><summary>{title}</summary>{content}{closeButton}</details>'
            
            articles.append({
                    'index':len(articles),
                    'date':pubDate,
                    'link':link,
                    'content':content
                })
        
        return {
            'buildDate':buildDate,
            'items':articles
        }
    
    def feedToHTML(self, feed):
        if 'success' not in feed or not feed['success']: return ''
        name = feed['name']
        id = feed['id']
        articles = feed['parsedFeed']['items']
        
        # Create buttons
        newerButton = createButton(f'newerButton-{id}', 'Newer', f'onArticleNavClick(\'{id}\', -1)', True)
        olderButton = createButton(f'olderButton-{id}', 'Older', f'onArticleNavClick(\'{id}\', 1)')
        
        # Create article dropdown
        options = []
        for a in articles:
            options.append(f'<option value="{a["index"]}">{a["date"]}</option>')
        
        selectHTML = f'<select id="dropdown-{id}" onchange="onArticleChange(this)">{"".join(options)}</select>'
        
        titleHTML = f'<div class="page-title">{name}</div>'
        
        # Combine into a header
        headerHTML = f'<div class="article-header">{titleHTML}{olderButton}{selectHTML}{newerButton}</div>'
        
        # Create the image
        articleHTML = f'<div id="article-{id}" class="article">{articles[0]["content"]}</div>'
        
        # Combine
        return f'<div id="feed-{id}" class="page-Div">{headerHTML}{articleHTML}</div>'
    
    '''
    Only need the image source
    '''
    def itemToJavascript(self, article):
        content = article['content']
        b = base64.b64encode(bytes(content, 'utf-8')) # bytes
        base64_str = b.decode('utf-8')
        return f'{{"content":"{base64_str}"}}'
    
class ComicsLoader(FeedLoader):
    def __init__(self, json_data):
        super().__init__(json_data, 'comic_feeds')
    
    def parseXML(self, tree, id):
        try:
            buildDate = xmlDateToString(tree, './channel/lastBuildDate')
        except:
            buildDate = 'today'
        
        comicStrips = []
        items = tree.findall('./channel/item')
        feedTitle = tree.find('./channel/title').text
        errorMessages = []
        for cidx, i in enumerate(items):
            pubDate = xmlDateToString(i, 'pubDate')
            link = i.find('link').text
            
            description = i.find('description')
            if description is None or description.text is None:
                description = i.find('content')
            if description is None:
                print(f'Cannot parse xml for strip {cidx+1} in feed "{feedTitle}"')
                continue
            
            description = stringToHTML(description.text)
            src = description.xpath('//div//img/@src')
            if len(src) == 0:
                src = description.xpath('@src')
            if len(src) == 0:
                # This is for Swan Boy specifically
                try:
                    content = i.find('content')
                    content = stringToHTML(content.text)
                    src = content.xpath('//img/@data-large-file')
                except:
                    src = []
            if len(src) == 0:
                # Poorly Drawn Lines
                try:
                    content = stringToHTML(i.find('content').text)
                    src = content.xpath('//img/@src')
                except:
                    src = []
            if len(src) == 0:
                # Blind Alley
                try:
                    src = stringToHTML(i.find('description').text)
                    src = src.xpath('//img/@src')
                except Exception as e:
                    print(e)
                    src = []
            if len(src) == 0:
                errorMessages.append(
                    f'Cannot find image source {cidx+1} in feed "{feedTitle}"'
                )
                continue
            src = src[0]
            
            comicStrips.append({
                    'index':len(comicStrips),
                    'date':pubDate,
                    'src':src,
                    'link':link
                })
        if len(errorMessages) > 0:
            print(f'{feedTitle}: Unable to find source for {len(errorMessages)} images')
        
        
        return {
            'buildDate':buildDate,
            'items':comicStrips
        }
    
    def feedToHTML(self, feed):
        if 'success' not in feed or not feed['success']: return ''
        name = feed['name']
        id = feed['id']
        strips = feed['parsedFeed']['items']
        
        if len(strips) == 0:
            return '<div id="feed-{id}" class="comic-Div">Unable to load any strips for {name}</div>'
        
        newerButton = createButton(f'newerButton-{id}', 'Newer', f'onComicNavClick(\'{id}\', -1)', True)
        olderButton = createButton(f'olderButton-{id}', 'Older', f'onComicNavClick(\'{id}\', 1)')
        
        # Create strip dropdown
        options = []
        for s in strips:
            options.append(f'<option value="{s["index"]}">{s["date"]}</option>')
        selectHTML = f'<select id="dropdown-{id}" onchange="onComicChange(this)">{"".join(options)}</select>'
        
        titleHTML = f'<div class="comic-title">{name}</div>'
        
        # Combine into a header
        headerHTML = f'<div class="comic-header">{titleHTML}{olderButton}{selectHTML}{newerButton}</div>'
        
        # Create the image
        stripHTML = f'<div id="strip-{id}" class="comic-strip"><img id="stripImage-{id}" class="comic-img unexpanded-img" src="{strips[0]["src"]}" ></div>'
        
        # Combine
        return f'<div id="feed-{id}" class="comic-Div">{headerHTML}{stripHTML}</div>'
    
    '''
    Only need the image source
    '''
    def itemToJavascript(self, strip):
        return f'{{"imageSource":"{strip["src"]}"}}'