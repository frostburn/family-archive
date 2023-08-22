# family-archive

File-system based HTTP server for a large amount of photos and videos for a limited audience.

## Goals

* Easily archivable: Just `rsync` the main folder from your server to cold storage media.
* Human-readable: No fancy binaries besides images and videos.
* No cold storage dependencies: All archived information should be available 100 years into the future.

## Features

* Albums: Folders are treated as albums with name, date and location
* Sorting albums: Order of images stored as separate metadata
* Hiding images: Bad shots can be hidden from the web view

## Not implemented (yet?)

* User profiles with access controls
* Tagging people in the images
* EXIF tagging for date taken/digitized and geolocation
