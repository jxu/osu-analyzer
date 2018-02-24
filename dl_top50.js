// Downloads top 50 replays
// Paste into console and run. Be sure to unblock pop-ups
function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
var l = document.links;
for(var i=0; i<l.length; i++) {
    if (l[i].href.includes("osu-getreplay")) {
        window.open(l[i].href);
        await sleep(1000);
    }
}