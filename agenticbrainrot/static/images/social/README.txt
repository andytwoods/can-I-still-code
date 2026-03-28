Favicon Pack  –  YourBrandOrSiteName
=====================================

FILES INCLUDED
 – favicon-16x16.png
 – favicon-32x32.png
 – apple-touch-icon.png
 – android-chrome-192x192.png
 – android-chrome-512x512.png
 – mstile-150x150.png
 – mstile-310x310.png
 – favicon.ico
 – site.webmanifest

WHERE TO UPLOAD
1) Create a folder on your site: /assets/img/favicons/
2) Upload ALL files from this ZIP into that folder.

ADD THIS TO <head>
-------------------------------------
<link rel="icon" href="/assets/img/favicons/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/favicons/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/img/favicons/favicon-16x16.png">
<link rel="apple-touch-icon" href="/assets/img/favicons/apple-touch-icon.png">
<link rel="manifest" href="/assets/img/favicons/site.webmanifest">

OPTIONAL: PWA manifest (not required for favicons)
-------------------------------------
Unzip and copy site.webmanifest alongside your icons for a better Add-to-Home experience.
Or copy the JSON below into a new file named site.webmanifest:

        {
          "name": "YourBrandOrSiteName",
          "short_name": "YourBrandOrSiteName",
          "icons": [
            { "src": "android-chrome-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" },
            { "src": "android-chrome-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
          ],
          "theme_color": "#f2f2f2",
          "background_color": "#f2f2f2",
          "display": "standalone"
        }

OPTIONAL: Safari pinned tab (monochrome SVG)
-------------------------------------
Provide a 1-color SVG named safari-pinned-tab.svg and add this in <head>:
<link rel="mask-icon" href="/assets/img/favicons/safari-pinned-tab.svg" color="#000000">

CACHE & VERIFICATION
- Clear browser cache and reload your site.
- On Android, long-press the home screen → Add to Home screen to see the Apple/Android icon.
- Use dev tools (Application tab) to verify icons.
