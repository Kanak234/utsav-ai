// Registers the service worker (makes this an installable PWA for the Microsoft Store)
// and swaps to the offline page if there is no internet.
"use strict";
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {}); // the app still works without it
}
const statusEl = document.getElementById("status");
const frame = document.getElementById("planner");
frame.addEventListener("load", () => { statusEl.hidden = true; });
function checkOnline() {
  if (!navigator.onLine) window.location.replace("offline.html");
}
window.addEventListener("offline", checkOnline);
checkOnline();
