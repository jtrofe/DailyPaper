from feedLoader import *
from numpy import array_split
import json

'''
Turn a list of feeds into N columns of HTML
'''
def chunkify(l, N):
    return [''.join(o['html'] for o in x) for x in array_split(l, N)]

'''
- Read all the feeds
- Turn them into html
- Paste that html into the base file
'''
def CreatePaperHTML():
    # Load the base HTML file
    baseHTML = open('paper.html', encoding='utf-8').read()
    
    # Load the json data
    with open('comics.json') as f:
        jsonData = json.load(f)
    
    comicFeeds = ComicsLoader(jsonData)
    pageFeeds = PageLoader(jsonData)
    
    columns = 3
    
    comicHTML = chunkify(comicFeeds, columns)
    articleHTML = chunkify(pageFeeds, columns)
    
    cellHTML = ''.join(f'<td>{comicHTML[i]+articleHTML[i]}</td>' for i in range(columns))
    
    # Create the table
    html = f'<table><tr>{cellHTML}</tr></table>'
    
    baseHTML = baseHTML.replace('<div id="content">\n\t\t</div>', f'<div id="content">{html}</div>')
    
    # Create javascript
    comicJavascript = comicFeeds.ToJavascript('comicFeeds')
    baseHTML = baseHTML.replace('</head>', f'<script>{comicJavascript}</script></head>')
    
    articleJavascript = pageFeeds.ToJavascript('articleFeeds')
    baseHTML = baseHTML.replace('</head>', f'\n<script>{articleJavascript}</script></head>')
    
    return baseHTML
