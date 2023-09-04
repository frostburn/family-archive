# family-archive

File-system based HTTP server for a large amount of photos, videos and audio for a limited audience.

## Goals

* Easily archivable: Just `rsync` the main folder from your server to cold storage media.
* Human-readable: No fancy binaries besides images, videos and audio.
* No cold storage dependencies: All archived information should be readable 50 years into the future.

## Features

* Albums: Folders are treated as albums with name, date and location
* Commenting: Viewed albums and media can be commented on
* Sorting albums: Order of images stored as separate metadata
* Hiding images: Bad shots can be hidden from the web view
* Password protected user profiles

## Not implemented (yet?)

* Access controls
* Tagging people in the images
* EXIF tagging for date taken/digitized and geolocation
