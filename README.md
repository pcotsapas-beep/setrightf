# Set Right Flatwork LLC — Website

A complete static website: 9 routes, a custom 404 page, the brand assets and the SEO configuration. It is plain HTML, CSS and JavaScript with no framework, so it can be hosted anywhere or imported into another builder.

```
build.py          Generates every page from shared templates (edit content here)
static/           Source assets: CSS, JS, images, logo, favicons
dist/             The finished website: upload this folder's contents
```

## Pages

| Route | Page |
|---|---|
| `/` | Home |
| `/services` | Services (anchors: `#driveways` `#patios` `#walkways` `#slabs` `#garage-floors` `#commercial` `#more`) |
| `/products` | Concrete solutions, planning prices, budget calculator |
| `/projects` | Our Work gallery (filters plus a larger image viewer) |
| `/about` | Company story, owner, mission, vision, values |
| `/contact` | Contact details, estimate form, office location (`#estimate`) |
| `/privacy-policy` | Privacy Policy (full text) |
| `/refund-policy` | Refund & Cancellation Policy (full text) |
| `/terms-and-conditions` | Terms and Conditions (full text) |
| `/404.html` | Not-found page (noindex) |

Each route is a folder with an `index.html` inside, so `/services` works on Netlify, Vercel, Cloudflare Pages, Apache, Nginx and most other hosts with no extra configuration.

## Preview locally

```
cd dist
python3 -m http.server 8000
# open http://localhost:8000
```

Opening the HTML files directly (`file://`) will not work, because links are root-relative.

## Before launch: 4 things to connect

### 1. Production domain — configured: https://setrightflatwork.com
`build.py` now defaults to the official domain and email, so a plain `python3 build.py` produces the production build:
- `/sitemap.xml` lists all 9 routes on `https://setrightflatwork.com` (re-run the build after content changes to refresh `lastmod`)
- `/robots.txt` allows all crawlers and includes `Sitemap: https://setrightflatwork.com/sitemap.xml`
- every page has an HTTPS canonical URL, `og:url`, `og:image` and Twitter image on the official domain
- the JSON-LD (GeneralContractor/Organization + WebSite) includes the URL, email, phone, address and owner, with no ratings, reviews, hours or certifications

The canonical form is **https://setrightflatwork.com** (no `www`, no trailing slash except the home page `/`). Configure hosting to match; see "Domain & hosting checklist" below.

#### Domain & hosting checklist (must be done outside this code)
1. **Point DNS at your host.** Add the A/ALIAS/CNAME records your host specifies for `setrightflatwork.com`, plus a `www` record.
2. **Enable HTTPS.** Issue the SSL certificate for both `setrightflatwork.com` and `www.setrightflatwork.com` (most hosts do this automatically once DNS resolves), and turn on "force HTTPS".
3. **Redirect `www` → apex.** `https://www.setrightflatwork.com/*` should 301-redirect to `https://setrightflatwork.com/*`.
4. **Serve pages without a trailing slash.** Confirm `https://setrightflatwork.com/services` loads with status 200 and no redirect to `/services/`. On Vercel the included `vercel.json` handles this; on other hosts check the "pretty URLs" / trailing-slash setting.
5. **Upload `dist/` as the site root.** Do not deploy to a preview URL and leave it as production; canonicals always point to the official domain.
6. **Check after launch:** open `/robots.txt`, `/sitemap.xml` and view-source on any page to confirm the canonical tag.
7. **Email:** make sure `info@setrightflatwork.com` actually receives mail (MX records with your email provider) before the address is relied on publicly.

### 2. Contact form backend
The form validates input, but **it does not send anything until an endpoint is set.** Until then it shows a visible notice and tells visitors to call 650-250-6345 or email info@setrightflatwork.com. It never claims a message was sent.

To connect it, create a form endpoint with any service that accepts a standard POST (Formspree, Basin, Getform, Netlify Forms, or your own server). Then rebuild:

```
python3 build.py --form-endpoint https://formspree.io/f/XXXXXXX
```

The notice then disappears, and successful or failed submissions show a matching message. Field names sent: `name, email, phone, project_type, location, size, description, consent`.

### 3. Google Search Console
Add the property `https://setrightflatwork.com` (or a Domain property for `setrightflatwork.com`), then choose one verification method:
- **HTML tag:** copy only the `content="..."` value Google gives you and rebuild with `--gsc-token THAT_VALUE`. It is added to every page's `<head>`.
- **DNS record** (recommended, covers the whole domain): add the TXT record at your domain registrar. No site change is needed.

Then submit `https://setrightflatwork.com/sitemap.xml` under **Sitemaps** in Search Console.

### 4. Legal review
The Privacy, Refund and Terms pages reproduce the supplied templates in full. They are business-oriented starting templates and **have not been reviewed by an attorney.** Have them reviewed before publication.

## Optional settings

All options can also be set as environment variables (`SITE_URL`, `FORM_ENDPOINT`, `GSC_TOKEN`, `GBP_URL`, `CONTACT_EMAIL`).

| Option | Effect |
|---|---|
| `--email` | Defaults to `info@setrightflatwork.com`. Shown as plain text (no `mailto:`) in the contact card, footer, About page, all three policies and structured data. |
| `--gbp-url https://...` | Adds a "Read our reviews on Google" button to the Customer Feedback section. No link is shown while empty. |
| `SOCIAL` list in `build.py` | Add `("Facebook", "https://...")` pairs and a Follow column appears in the footer. It is hidden while empty. |

## Content notes

- **Phone, email, website and address** are plain text everywhere. There are no `tel:` or `mailto:` links, and a `format-detection` meta tag stops phones from turning them into links automatically.
- **No invented facts.** There are no reviews, ratings, opening hours, licenses, insurance claims, founding dates or staff bios. The structured data contains only verified business details.
- **Photos are illustrative.** The home page, Our Work and the Terms all say the photos are not company projects. The Our Work page has a section reserved for real project photos (search `future-frame` in `build.py`).
- **Owner photo:** the About page shows a typographic monogram. To use a real photo, replace the `.owner-plate` element (marked with a comment in `build.py`).
- **Reviews:** add verified reviews as `<blockquote>` elements where the comment in the home page's Customer Feedback section indicates.

## Images

### Hero photograph (centralized)
The main hero photo is defined once in `build.py`:

```python
HERO_IMG = "set-right-driveway-hero"
IMG_SIZES = { HERO_IMG: ((800, 1200, 1759), 1759, 894) }
```

It is used for the **home page hero**, the **Services page closing banner**, the **Our Work gallery** ("Freshly finished driveway") and the **social preview image** (`assets/brand/og-image.jpg`). To change it, replace the files and update these two lines. Every page then follows.

- Original, unmodified source: `static/assets/img/set-right-driveway-hero.png` (1759 × 894)
- Responsive versions: `set-right-driveway-hero-{800,1200,1759}.{jpg,webp}`. Browsers pick the right size automatically.
- Crop focal point: `.hero-media img { object-position: 60% 60%; }` in `site.css`, which keeps the fresh slab, forms and garage beside the headline on desktop. On phones the full photo shows above the text.

To regenerate the versions from a new original:

```python
from PIL import Image
im = Image.open("static/assets/img/set-right-driveway-hero.png").convert("RGB")
for w in (800, 1200, 1759):            # widths must match IMG_SIZES
    r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    r.save(f"static/assets/img/set-right-driveway-hero-{w}.jpg", quality=84, optimize=True, progressive=True)
    r.save(f"static/assets/img/set-right-driveway-hero-{w}.webp", quality=82, method=6)
```

### Other photographs
The remaining eight photos (`02`–`09`) are **414 × 414 px** originals with 414 and 900 px versions, and look soft on large screens. To upgrade one, add its larger widths to `IMG_SIZES` (as with the hero) and generate the matching `-{width}.jpg/.webp` files.

## Brand assets (`static/assets/brand/`)

| File | Use |
|---|---|
| `mark.svg` / `mark-light.svg` | Symbol on light / dark backgrounds |
| `logo-on-light.svg` / `logo-on-dark.svg` | Full lockup (text renders in Archivo where installed) |
| `og-image.jpg` | 1200 × 630 social preview |
| `/favicon.ico`, `/favicon-48.png`, `/icon-192.png`, `/icon-512.png`, `/apple-touch-icon.png` | Favicons and app icons (referenced in every page head and in `site.webmanifest`) |

Palette: Charcoal `#242629` · Concrete Gray `#74777A` · Off-White `#F3F1EC` · Safety Orange `#F47721` · Deep Black `#17191B` · White `#FFFFFF`.
Type: Archivo (expanded, heavy) for headings and Public Sans for body text, both loaded from Google Fonts.
Orange buttons use black text: white on `#F47721` does not meet accessibility contrast requirements.
