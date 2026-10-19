# NFC business cards

One repo, one GitHub Pages site, one page per person:

```
https://<github-username>.github.io/<repo-name>/<person>/
```

## Add or edit a person

1. Create `people/<person>.json`. The file name becomes the URL, so use lowercase letters, digits and dashes only, e.g. `people/jane-doe.json` → `/jane-doe/`.

   ```json
   {
     "firstName": "Jane",
     "lastName": "Doe",
     "title": "Portfolio Manager",
     "email": "jane.doe@example.com",
     "phone": "+44 20 7946 0000",
     "linkedin": "https://www.linkedin.com/in/example"
   }
   ```

   `title` is optional. Write `phone` in international format (with `+` and country code) so it dials from any country. Add `"company": "..."` to override the company name in `site.json` for one person.

2. Run `python3 build.py`.
3. Commit and push, including the `docs/` folder.

To remove someone, delete their JSON file and rebuild. Never edit `docs/` by hand: every build regenerates it from scratch.

## Files

| Path | What it is |
| --- | --- |
| `site.json` | Company name, logo, accent color. `baseUrl` (optional): the site's full URL, used for link previews in iMessage/WhatsApp. |
| `people/*.json` | One file per person |
| `templates/card.html` | The page design, shared by everyone |
| `build.py` | Generates `docs/` (pages + `.vcf` contact files) |
| `docs/` | The built site that GitHub Pages serves |

## GitHub Pages setup (once)

Repo → Settings → Pages → Source: "Deploy from a branch" → Branch `main`, folder `/docs`.

## Preview locally

```bash
python3 build.py && python3 -m http.server 8080 --directory docs
```

Then open http://localhost:8080/rush/.

## Live cards

- https://andreamonsa.github.io/card/rush/
- https://andreamonsa.github.io/card/stefano/

## Writing the NFC chip

Write a single URL record with the person's full URL, including the trailing slash. Test it on an iPhone and on an Android phone, then lock the chip if you want to stop it being overwritten. **Locking is permanent.**

## Search engines

Every page has `noindex, nofollow` meta tags, so the pages stay out of search results.
