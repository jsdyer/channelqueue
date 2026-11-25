# Channel Queue

A private research desk for public YouTube videos: collect sources, organize a learning queue, write timestamp notes, and choose where to resume. [Use Channel Queue](https://coolcode.ca/channelqueue/).

<!-- coolcode:guide -->
Paste a public video, playlist or channel URL, a channel @handle, or a video ID. Explore loaded videos, filter by keywords or length, then add bookmarks to your own learning queue with topics, manual resume positions and timestamp notes. Saved workspace files contain your annotations and links; refresh YouTube details when reopening them. Playback uses the official YouTube player and restricted or child-directed videos open on YouTube instead.
<!-- /coolcode:guide -->

## Use it

1. Read and agree to the prominently displayed privacy policy and terms. No YouTube login is requested.
2. Open a public channel `@handle`, `/channel/ID`, playlist URL or video URL. You can also search for channels by any subject. The shared global-search quota is limited; direct source links are usually more efficient.
3. Channel lookups resolve the uploads playlist. Playlist pages load 50 entries at a time, and **Load next playlist page** continues when a token exists. Private/deleted/unavailable entries may be omitted. The view is capped at the configured 500 available videos, not claimed as a complete channel archive.
4. Filter loaded videos by keywords and maximum minutes. Unknown lengths have their own option. Add videos to a learning queue, then organize with your own topics, labels, completion marks and note text.
5. Use the player’s displayed timestamp to add a note or manually save a resume position. Clicking a note checks the video again and loads the official player at that timestamp. Playback does not auto-start. The app does not record viewing history, infer completion or download videos/audio.
6. Remember the workspace only if desired. Otherwise it exists in the current tab. Export JSON to transfer your own bookmarks and annotations. A workspace is limited to 2 MB of serialized user data so every exported backup can be reopened; edits that exceed that budget are rolled back with a visible message. Opening a file replaces the current workspace. Keep a backup before clearing browser data.

A useful example: collect a public home-networking playlist, choose videos under 20 minutes, label the queue topic “Home lab”, and note the timestamp where a VLAN configuration is explained. Your notes remain useful when a video is later unavailable; a removed video cannot be played here.

## Source, privacy and caching

Public metadata comes from [YouTube Data API v3](https://developers.google.com/youtube/v3) through a protected CoolCode gateway. YouTube supplies titles, channels, descriptions, thumbnails, durations and playback status. Topics, labels, completion and notes are explicitly your own data, not YouTube metrics or rankings. No popularity score, scraped source, recommendation feed or private account synchronization is implemented.

The browser keeps API metadata only in tab memory and evicts it after 29 days (also checked when it is accessed). **No API title, description, thumbnail or duration is saved to localStorage or exported workspaces.** Saved records are user-selected canonical bookmark/source URLs and user annotations. A restored workspace shows links and your labels; use **Refresh YouTube details** to fetch current metadata. Imports whitelist only those user fields. The gateway must separately ensure its provider cache has a lifetime under 30 days.

Every embed first checks `videos.list` with `status` to verify availability, `embeddable` and `madeForKids`. If the video is child-directed or that flag cannot be verified, only a YouTube link is offered. The official `youtube-nocookie.com` player loads only by user action, with no autoplay, at least a 200×200 viewport, and no overlay or hidden media. YouTube can still collect playback/device information and serve ads under its own policy. Metadata thumbnails contact YouTube image hosts.

The in-app policy links the [Google Privacy Policy](https://policies.google.com/privacy) and [YouTube Terms of Service](https://www.youtube.com/t/terms). Users must agree before API/player functionality is available. Search terms and public IDs/handles go to the gateway and YouTube; notes stay on the user’s device. Optional local persistence uses `coolcode:channelqueue:workspace:v1`. **Clear workspace** removes local records immediately; it does not change YouTube data or delete separately exported files. The shared CoolCode counter records aggregate opens independently of workspace contents.

## API key: put it in the protected Worker

**Do not put a YouTube API key in this repository, `web/`, GitHub Pages variables, JavaScript, or a public artifact.** Add `YOUTUBE_API_KEY` as a **secret** binding on the existing shared Cloudflare Worker `coolcode-visitor-api` (Settings → Variables and Secrets), then deploy the gateway code supplied in the main CoolCode repository. In Google Cloud, enable YouTube Data API v3 for that key’s project and restrict the key to that API. Repository secrets alone do not configure this static application.

The public `web/config.json` contains `api_base`, initially `https://coolcode-visitor-api.jeffdyer.workers.dev`. Missing credentials and exhausted quotas are shown as service errors, without invented data. Global channel search is an explicit action and uses the owner’s limited shared search allowance; it is never requested automatically on page load or keystrokes.

| Read-only route under `/api/channelqueue/` | Inputs | Upstream operation |
| --- | --- | --- |
| `channel` | `id` or `handle` | `channels.list`, snippet + contentDetails |
| `playlist` | `id`, optional `pageToken` | `playlistItems.list`, snippet + contentDetails, up to 50 |
| `videos` | comma-separated `ids`, up to 50 | `videos.list`, snippet + contentDetails + status |
| `search` | `q` | `search.list`, type channel, up to 10 |

Success: `{ "fetched_at": "ISO timestamp", "data": { "items": [], "nextPageToken": "optional" } }`. Failure: non-2xx `{ "error": { "code": "...", "message": "..." } }`. The gateway validates inputs and allows the CoolCode origin, protects the key, bounds requests and caches public metadata appropriately. It must preserve the `status` fields used by embedding checks.

## Expand or customize

Edit `web/config.json`: append `"Urban gardening"` to `starter_topics` to add a search shortcut, or adjust `max_loaded_videos` between 50 and 1000. User-entered subjects, handles and links work independently of the defaults. Counts and filters derive from fetched records. Larger view limits consume more playlist/detail requests; they do not bypass provider quota or permissions. `api_base` changes the public protected gateway address, never a credential.

Run checks below, then push to `main` to trigger **Browser tool · Check and publish**. Set **Settings → Pages → Source → GitHub Actions**. Successful main runs publish the project subpath without a CNAME. There is no scheduled collector or refresh workflow: source opening, pagination, detail refresh and playback checks fetch metadata on demand. A frontend build does not prove gateway secrets are configured.

Update the hub guide and `tool.json` registration, generated Worker ID list, sitemap and watchdog target under the [mandatory tool lifecycle](https://github.com/jsdyer/jsdyer.github.io/blob/main/docs/tool-lifecycle.md). No per-app data schedule needs to be added to the watchdog. Live gateway readiness must be verified after the owner deploys the Worker and secret.

## Development

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

The static build is offline and dependency-free. `dist/` is generated. Browser tests use fixture responses matching official API shapes and verify consent, channel/playlist paging, notes, persistence boundaries, child-directed embed handling, exports and mobile overflow. Install `tests/browser-requirements.txt`, then run `CHROMIUM_PATH=/path/to/google-chrome python3 tests/browser_smoke.py`. CI uses installed Chrome on Ubuntu 24.04 and uploads screenshots for review.
