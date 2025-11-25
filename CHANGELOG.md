## [0.1.26] - 26.11.2025
### Changed
- Added real-time log updates via WebSocket [#16](https://github.com/JoelHer/Oculex/issues/16) ([713643c](https://github.com/JoelHer/Oculex/commit/713643ca6554c0a43bd986dbf9df096ec45f95ff))
- Execution logger now broadcasts logs to the websocket [#16](https://github.com/JoelHer/Oculex/issues/16) ([7376a82](https://github.com/JoelHer/Oculex/commit/865d4de5e274244a6a5014ca4e7a390fc7376a82))
### Fixed
- StreamHandler logs to proper log levels now. [#16](https://github.com/JoelHer/Oculex/issues/16) ([72f7228](https://github.com/JoelHer/Oculex/commit/72f722830b84a2229adebf0f0ccb3d48e9d97b79))
### Removed 
- Removed auto-refresh UI controls and related logic in the execution logger [#16](https://github.com/JoelHer/Oculex/issues/16) ([713643c](https://github.com/JoelHer/Oculex/commit/713643ca6554c0a43bd986dbf9df096ec45f95ff))

## [0.1.25] - 24.11.2025
### Added
- Added OCR execution logger, with auto refresh and debug level sorting [#16](https://github.com/JoelHer/Oculex/issues/16) ([9a6d177](https://github.com/JoelHer/Oculex/commit/9a6d177bb0bd9789dc973a74c357977e33efa32c))
 

## [0.1.24] - 7.10.2025
### Changed
- Updated the rest of the UI to the new UI Standard. [#13](https://github.com/JoelHer/Oculex/issues/13) ([0f22011](https://github.com/JoelHer/Oculex/commit/0f22011e6feb064541d4d233ddf5d73726e85229))

## [0.1.23] - 4.10.2025
### Changed
- Images automatically refresh when setting has been saved in the parser. [#23](https://github.com/JoelHer/Oculex/issues/23) ([6bd9d8b](https://github.com/JoelHer/Oculex/commit/6bd9d8b87f1aa1913d2ce7c1d47a07397166b7a4))
- Box IDs are now based on total number of boxes ([03e64b6](https://github.com/JoelHer/Oculex/commit/03e64b6ce4b234b428ec542cfed001be2973cc97))
- Disabled frame grabbing caching for now, due to bug ([2fc46f8](https://github.com/JoelHer/Oculex/commit/2fc46f8dabb98be01d6210136a3ba5513cc6888f))

## [0.1.22] - 3.10.2025
### Fixed
- Fixed bug in scheduler, where it was not possible to save custom cron expressions.  ([be10649](https://github.com/JoelHer/Oculex/commit/be10649ab09b851ad815d745b0e9955a31f7badd))
## [0.1.21] - 3.10.2025
### UI
- Improved responsiveness and added scrolling [#18](https://github.com/JoelHer/Oculex/issues/18) ([bbf3ca2](https://github.com/JoelHer/Oculex/commit/bbf3ca2039d3135f1d1dfe1167039b83083df116))
- Added skeleton loading to images in the stream editor [#5](https://github.com/JoelHer/Oculex/issues/5) ([e0f034d](https://github.com/JoelHer/Oculex/commit/e0f034d2d04fcac261ee0e694d80ef1ca907d139))

## [0.1.20] - 30.09.2025
### Changed
- Changes to Dockerfile ([7b31b8d](https://github.com/JoelHer/Oculex/commit/7b31b8daa865524d929f83d0622ea280e0fefdc1))

## [0.1.19] - 28.09.2025
### Fixed
- Fixed bug in the scheduler, which caused new streams to not be added to the cron job list ([ed43e3a](https://github.com/JoelHer/Oculex/commit/ed43e3a1bd137142852201edd23a0c8958ffeb74))


# Start of Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"TBR": To be released
"TBW": To be written
