function onComicChange(el){
	var id = el.id.replace("dropdown-", "");
	var comicIndex = el.value;
	
	var strip = globalThis.comicFeeds[id]
						.items[comicIndex];
	
	document.getElementById("stripImage-"+id).src = strip.imageSource;
	
	// Set the class of the "older" and "newer" buttons
	var stripCount = el.length;
	
	var olderButton = document.getElementById("olderButton-"+id);
	var newerButton = document.getElementById("newerButton-"+id);
	
	newerButton.disabled = el.value == 0;
	olderButton.disabled = el.value == el.length-1;
	
	// Create venobox
	wrapImages(document.getElementById("strip-"+id));
}

// Javascript's built in "atob()" function doesn't handle the utf-8 characters correctly
// https://stackoverflow.com/questions/30106476/using-javascripts-atob-to-decode-base64-doesnt-properly-decode-utf-8-strings
const base64Decode = base64EncodedString =>
  new TextDecoder().decode(Uint8Array.from(atob(base64EncodedString), m => m.charCodeAt(0)));

/*
When an article is changed the images
they need to added to venobox
*/
function onArticleChange(el){
	var id = el.id.replace("dropdown-", "");
	var articleIndex = el.value;
	
	var article = globalThis.articleFeeds[id]
						.items[articleIndex];
	var articleHTML = base64Decode(article["content"]);
	document.getElementById("article-"+id).innerHTML = articleHTML;
	
	// Set the class of the "older" and "newer" buttons
	var stripCount = el.length;
	
	var olderButton = document.getElementById("olderButton-"+id);
	var newerButton = document.getElementById("newerButton-"+id);
	
	newerButton.disabled = el.value == 0;
	olderButton.disabled = el.value == el.length-1;
	
	// Create venobox
	wrapImages(document.getElementById("article-"+id));
}

function closeDetail(detailsElement) {
    detailsElement.removeAttribute("open");
    window.location = '#details_' + detailsElement.id;
}

/*
Load the next strip in the feed.
`dir` is +1 for older and -1 for newer
*/
function onComicNavClick(id, dir){
	if(dir == 0) return;
	if(dir < -1) dir = -1
	if(dir > 1) dir = 1
	
	document.getElementById("stripImage-"+id).src = "loading.gif";
	
	setTimeout(function() {
		var select = document.getElementById("dropdown-"+id);
		var currentIndex = select.selectedIndex;
		
		if(dir == -1 && currentIndex == 0) return
		if(dir == 1 && currentIndex > select.length-2) return;
		select.selectedIndex = currentIndex + dir;
		select.onchange();
	}, 0);
}

/*
Load the next article in the feed.
`dir` is +1 for older and -1 for newer
*/
function onArticleNavClick(id, dir){
	if(dir == 0) return;
	if(dir < -1) dir = -1
	if(dir > 1) dir = 1
	
	document.getElementById("article-"+id).innerHTML = '<div>Loading...</div>'
	
	setTimeout(function() {
		var select = document.getElementById("dropdown-"+id);
		var currentIndex = select.selectedIndex;
		
		if(dir == -1 && currentIndex == 0) return
		if(dir == 1 && currentIndex > select.length-2) return;
		select.selectedIndex = currentIndex + dir;
		select.onchange();
	}, 0);
}

/*
Wrap images with the venobox stuff
*/
function wrapImages(el){
	var images = el.getElementsByTagName("img");
	
	for(var i=0;i<images.length;i++){
		var image = images[i];
		
		var venoWrapper = document.createElement("a");
		venoWrapper.href = image.src;
		venoWrapper.classList.add("expandable");
		
		venoWrapper.innerHTML = image.outerHTML;
		
		image.parentNode.replaceChild(venoWrapper, image);
	}
	globalThis.veno = new VenoBox({
		selector: ".expandable"
	});
}

window.onload = function() {
	wrapImages(document);
};