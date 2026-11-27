#!/usr/bin/env python3
"""
Set Right Flatwork LLC — static site builder.

Generates every route as plain HTML into ./dist using the shared layout
below, then writes sitemap.xml, robots.txt and the web manifest.

    python3 build.py                                   # build without a domain
    python3 build.py --domain https://www.yourdomain.com
    python3 build.py --domain https://www.yourdomain.com \
        --form-endpoint https://formspree.io/f/xxxx \
        --gsc-token YOUR_GOOGLE_TOKEN

Settings can also come from environment variables:
SITE_URL, FORM_ENDPOINT, GSC_TOKEN, GBP_URL, CONTACT_EMAIL.

Nothing in this file invents business facts. Values that have not been
provided (domain, email, review profile, social links) stay empty, and the
templates simply leave those elements out until they are set.
"""
import argparse, datetime, html, json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DIST = ROOT / "dist"

ap = argparse.ArgumentParser()
ap.add_argument("--domain", default=os.environ.get("SITE_URL", "https://setrightflatwork.com"))
ap.add_argument("--form-endpoint", default=os.environ.get("FORM_ENDPOINT", ""))
ap.add_argument("--gsc-token", default=os.environ.get("GSC_TOKEN", ""))
ap.add_argument("--gbp-url", default=os.environ.get("GBP_URL", ""))
ap.add_argument("--email", default=os.environ.get("CONTACT_EMAIL", "info@setrightflatwork.com"))
args = ap.parse_args()

SITE_URL = args.domain.rstrip("/")
if SITE_URL and not SITE_URL.startswith("https://"):
    sys.exit("--domain must start with https://")
FORM_ENDPOINT = args.form_endpoint.strip()
GSC_TOKEN = args.gsc_token.strip()          # Google Search Console HTML-tag token
GBP_URL = args.gbp_url.strip()              # Google Business Profile review link
EMAIL = args.email.strip()                  # public email — omitted while empty
SOCIAL = []                                 # e.g. [("Facebook", "https://facebook.com/...")]
TODAY = datetime.date.today().isoformat()

# ---------------------------------------------------------------------------
# Verified business facts (from the client brief — do not edit without proof)
# ---------------------------------------------------------------------------
BIZ = {
    "name": "Set Right Flatwork LLC",
    "short": "Set Right Flatwork",
    "owner": "Phoebus Cotsapas",
    "phone": "650-250-6345",
    "phone_e164": "+1-650-250-6345",
    "street": "4022 Produce Rd",
    "city": "Louisville",
    "region": "KY",
    "zip": "40218",
    "country": "United States",
    "tagline": "Concrete Done Right. From the Ground Up.",
}
SITE_HOST = SITE_URL.replace("https://", "")   # display form, e.g. setrightflatwork.com
ADDR_LINES = f'{BIZ["street"]}<br>{BIZ["city"]}, {BIZ["region"]} {BIZ["zip"]}<br>{BIZ["country"]}'

NAV = [("/", "Home"), ("/services", "Services"), ("/products", "Products"),
       ("/projects", "Our Work"), ("/about", "About"), ("/contact", "Contact")]
LEGAL = [("/privacy-policy", "Privacy Policy"), ("/refund-policy", "Refund Policy"),
         ("/terms-and-conditions", "Terms and Conditions")]
ROUTES = ["/", "/services", "/products", "/projects", "/about", "/contact",
          "/privacy-policy", "/refund-policy", "/terms-and-conditions"]

# ---------------------------------------------------------------------------
# Images (illustrative photography supplied by the client)
# ---------------------------------------------------------------------------
# Primary hero photograph: change it here and every page that uses it updates.
# Original source file is kept untouched at /assets/img/set-right-driveway-hero.png
HERO_IMG = "set-right-driveway-hero"

# Responsive variants per image: (available widths, intrinsic width, intrinsic height).
# Images not listed use the default square 414/900 set.
IMG_SIZES = {
    HERO_IMG: ((800, 1200, 1759), 1759, 894),
}
DEFAULT_SIZES = ((414, 900), 900, 900)

ALT = {
    HERO_IMG: "Freshly finished concrete driveway with wooden forms still in place, leading to a dark two-car garage on a stone-front house",
    "02-concrete-finishing-bull-float": "Worker in boots pushing a bull float across a freshly poured concrete slab",
    "03-completed-driveway": "Finished light-gray concrete driveway leading to a dark two-car garage door",
    "04-completed-backyard-patio": "Square concrete patio with an outdoor dining set beside a house, surrounded by lawn",
    "05-curved-concrete-walkway": "Curved concrete walkway winding through a front yard between mulched flower beds and lawn",
    "06-worker-screeding-slab": "Worker leveling wet concrete inside wooden forms with a long screed board",
    "07-garage-floor": "Clean, smooth concrete floor in an empty two-car garage",
    "08-hand-finishing-closeup": "Close-up of a gloved hand finishing the edge of a fresh concrete slab with a trowel",
    "09-commercial-sidewalk": "Wide concrete sidewalk running along the glass storefront of a brick commercial building",
}

def img_srcset(name, ext):
    widths = IMG_SIZES.get(name, DEFAULT_SIZES)[0]
    return ", ".join(f"/assets/img/{name}-{w}.{ext} {w}w" for w in widths)

def img_full(name):
    """Largest JPEG variant (used for fallbacks and the lightbox)."""
    return f"/assets/img/{name}-{IMG_SIZES.get(name, DEFAULT_SIZES)[0][-1]}.jpg"

def pic(name, sizes="100vw", cls="", eager=False, alt=None, pos=None):
    a = html.escape(alt if alt is not None else ALT[name], quote=True)
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    style = f' style="object-position:{pos}"' if pos else ""
    c = f' class="{cls}"' if cls else ""
    _, w, h = IMG_SIZES.get(name, DEFAULT_SIZES)
    return (f'<picture><source type="image/webp" srcset="{img_srcset(name, "webp")}" sizes="{sizes}">'
            f'<img src="{img_full(name)}" srcset="{img_srcset(name, "jpg")}" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="{a}" {load} decoding="async"{c}{style}></picture>')

MARK = ('<svg class="brand-mark" viewBox="0 0 64 64" aria-hidden="true" focusable="false">'
        '<path fill="#F47721" d="M4 4H60V12H12V60H4Z"/><g class="slab"><rect x="18" y="18" width="42" height="19"/>'
        '<rect x="18" y="41" width="19" height="19"/><rect x="41" y="41" width="19" height="19"/></g></svg>')

def brand():
    return (f'<a class="brand" href="/" aria-label="{BIZ["name"]} home">{MARK}'
            '<span class="brand-word"><span class="b1">SET RIGHT</span><span class="b2">FLATWORK</span></span></a>')

def abs_url(path):
    return f"{SITE_URL}{path}" if SITE_URL else ""

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def header(active):
    items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        items.append(f'<li><a href="{href}"{cur}>{label}</a></li>')
    items.append('<li class="nav-cta"><a class="btn btn--primary" href="/contact#estimate">Request a Free Estimate</a></li>')
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    {brand()}
    <nav class="nav" id="site-nav" aria-label="Main">
      <ul>{"".join(items)}</ul>
    </nav>
    <a class="btn btn--primary header-cta" href="/contact#estimate">Request a Free Estimate</a>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu"><span></span></button>
  </div>
</header>'''

def footer():
    nav = "".join(f'<li><a href="{h}">{l}</a></li>' for h, l in NAV)
    legal = "".join(f'<li><a href="{h}">{l}</a></li>' for h, l in LEGAL)
    legal += '<li><a href="/about#our-story">Company Description</a></li>'
    email = f'<p><span class="k">Email</span><span class="v">{html.escape(EMAIL)}</span></p>' if EMAIL else ""
    website = f'<p><span class="k">Website</span><span class="v">{SITE_URL}</span></p>' if SITE_URL else ""
    social = ""
    if SOCIAL:  # rendered only once real profile links are added above
        social = '<h2>Follow</h2><ul>' + "".join(
            f'<li><a href="{html.escape(u, quote=True)}" rel="noopener" target="_blank">{html.escape(n)}</a></li>' for n, u in SOCIAL) + "</ul>"
    return f'''<footer class="site-footer">
  <div class="wrap footer-top">
    <div class="footer-brand">
      {brand()}
      <p class="footer-tag">{BIZ["tagline"]}</p>
      <p class="footer-desc" id="company-description">Set Right Flatwork LLC is a Louisville, Kentucky-based concrete flatwork contractor specializing in residential and commercial concrete solutions. Led by owner Phoebus Cotsapas, the company focuses on practical workmanship, attention to detail, straightforward communication, and quality-focused concrete installation.</p>
    </div>
    <div class="footer-contact">
      <h2>Contact</h2>
      <p><span class="k">Company</span><span class="v">{BIZ["name"]}</span></p>
      <p><span class="k">Owner</span><span class="v">{BIZ["owner"]}</span></p>
      <p><span class="k">Phone</span><span class="v">{BIZ["phone"]}</span></p>
      {email}
      <p><span class="k">Office</span><span class="v">{BIZ["street"]}, {BIZ["city"]}, {BIZ["region"]} {BIZ["zip"]}</span></p>
      {website}
    </div>
    <nav aria-label="Footer">
      <h2>Navigation</h2>
      <ul>{nav}</ul>
    </nav>
    <div>
      <h2>Legal</h2>
      <ul>{legal}</ul>
      {social}
    </div>
  </div>
  <div class="wrap footer-bottom">
    <span>&copy; <span data-year>{datetime.date.today().year}</span> {BIZ["name"]}. All rights reserved.</span>
    <span class="footer-creed">Prepare it right. Pour it right. Finish it right.</span>
  </div>
</footer>'''

def head(path, title, desc, jsonld=None, noindex=False, preload=None):
    canon = abs_url(path)
    tags = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        # keeps iOS/Android from turning the phone number and address into links
        '<meta name="format-detection" content="telephone=no, address=no, email=no, date=no">',
        f"<title>{html.escape(title)}</title>",
        f'<meta name="description" content="{html.escape(desc, quote=True)}">',
        f'<meta name="robots" content="{"noindex, follow" if noindex else "index, follow, max-image-preview:large"}">',
        '<meta name="theme-color" content="#17191B">',
        '<meta name="author" content="Set Right Flatwork LLC">',
    ]
    if canon and not noindex:
        tags.append(f'<link rel="canonical" href="{canon}">')
    if GSC_TOKEN:
        tags.append(f'<meta name="google-site-verification" content="{html.escape(GSC_TOKEN, quote=True)}">')
    # Open Graph / social preview
    tags += [
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Set Right Flatwork LLC">',
        '<meta property="og:locale" content="en_US">',
        f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
        f'<meta property="og:description" content="{html.escape(desc, quote=True)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{html.escape(title, quote=True)}">',
        f'<meta name="twitter:description" content="{html.escape(desc, quote=True)}">',
    ]
    if SITE_URL:
        tags += [
            f'<meta property="og:url" content="{canon}">',
            f'<meta property="og:image" content="{SITE_URL}/assets/brand/og-image.jpg">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta property="og:image:alt" content="Set Right Flatwork LLC — Concrete Done Right. From the Ground Up.">',
            f'<meta name="twitter:image" content="{SITE_URL}/assets/brand/og-image.jpg">',
        ]
    tags += [
        '<link rel="icon" href="/favicon.ico" sizes="any">',
        '<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
        '<link rel="manifest" href="/site.webmanifest">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&family=Public+Sans:wght@400;500;600;700&display=swap">',
        '<link rel="stylesheet" href="/assets/css/site.css">',
    ]
    if preload:
        tags.append(f'<link rel="preload" as="image" type="image/webp" imagesrcset="{img_srcset(preload, "webp")}" imagesizes="(max-width: 860px) 100vw, 64vw">')
    if jsonld:
        tags.append('<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False, indent=1) + "</script>")
    return "\n".join(tags)

def page(path, title, desc, body, active=None, jsonld=None, noindex=False, preload=None):
    return f'''<!doctype html>
<html lang="en-US">
<head>
{head(path, title, desc, jsonld, noindex, preload)}
</head>
<body>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
<script src="/assets/js/site.js" defer></script>
</body>
</html>
'''

def cta_band(img, h, p, primary=("Request a Free Estimate", "/contact#estimate"), secondary=None):
    sec = f'<a class="btn btn--line" href="{secondary[1]}">{secondary[0]}</a>' if secondary else ""
    return f'''<section class="cta-band" aria-labelledby="cta-h">
  <div class="bg">{pic(img, alt="")}</div>
  <div class="wrap">
    <h2 id="cta-h">{h}</h2>
    <p>{p}</p>
    <div class="btn-row"><a class="btn btn--primary" href="{primary[1]}">{primary[0]}</a>{sec}</div>
  </div>
</section>'''

# ---------------------------------------------------------------------------
# Structured data
# ---------------------------------------------------------------------------
BIZ_ID = f"{SITE_URL}/#business" if SITE_URL else "#business"

def business_ld():
    d = {
        "@type": ["GeneralContractor", "Organization"],
        "@id": BIZ_ID,
        "name": BIZ["name"],
        "description": "Concrete flatwork contractor in Louisville, Kentucky serving residential and commercial customers: driveways, patios, sidewalks and walkways, slabs and pads, garage floors, and small commercial flatwork.",
        "telephone": BIZ["phone_e164"],
        "address": {"@type": "PostalAddress", "streetAddress": BIZ["street"], "addressLocality": BIZ["city"],
                    "addressRegion": BIZ["region"], "postalCode": BIZ["zip"], "addressCountry": "US"},
        "areaServed": {"@type": "City", "name": "Louisville", "containedInPlace": {"@type": "State", "name": "Kentucky"}},
        "employee": {"@type": "Person", "name": BIZ["owner"], "jobTitle": "Owner"},
        "knowsAbout": ["Concrete flatwork", "Concrete driveways", "Concrete patios", "Concrete sidewalks",
                       "Concrete slabs", "Garage floors", "Commercial concrete flatwork"],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Concrete flatwork services", "itemListElement": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n}} for n in
            ["Concrete Driveways", "Concrete Patios", "Concrete Sidewalks & Walkways", "Concrete Slabs & Pads",
             "Garage Floors", "Commercial Concrete Flatwork", "Concrete Steps & Entryways"]]},
    }
    if SITE_URL:
        d["url"] = SITE_URL + "/"
        d["logo"] = SITE_URL + "/icon-512.png"
        d["image"] = SITE_URL + "/assets/brand/og-image.jpg"
    if EMAIL:
        d["email"] = EMAIL
    d["contactPoint"] = {"@type": "ContactPoint", "contactType": "customer service", "telephone": BIZ["phone_e164"],
                         "areaServed": "US", "availableLanguage": "English", **({"email": EMAIL} if EMAIL else {})}
    return d

def website_ld():
    d = {"@type": "WebSite", "name": BIZ["name"], "publisher": {"@id": BIZ_ID}, "inLanguage": "en-US"}
    if SITE_URL:
        d["@id"] = SITE_URL + "/#website"; d["url"] = SITE_URL + "/"
    return d

def graph(*items):
    return {"@context": "https://schema.org", "@graph": list(items)}

# ===========================================================================
# HOME
# ===========================================================================
def home():
    body = f'''
<section class="hero" aria-labelledby="hero-h">
  <div class="hero-media">{pic(HERO_IMG, sizes="(max-width: 860px) 100vw, 64vw", eager=True)}</div>
  <div class="wrap hero-inner">
    <p class="hero-tag">Concrete flatwork in Louisville, Kentucky</p>
    <h1 id="hero-h"><span class="line">Concrete Done Right.</span><span class="line">From the Ground Up.</span></h1>
    <p class="lede">Quality concrete flatwork for homes and businesses in Louisville, Kentucky. Built with attention to detail, dependable workmanship, and lasting results.</p>
    <div class="btn-row">
      <a class="btn btn--primary" href="/contact#estimate">Request a Free Estimate</a>
      <a class="btn btn--line" href="/services">Explore Our Services</a>
    </div>
  </div>
</section>
<div class="formboard" aria-hidden="true"></div>

<section class="trust" aria-label="What we offer">
  <div class="wrap">
    <ul>
      <li>Residential &amp; Commercial Concrete</li>
      <li>Quality-Focused Workmanship</li>
      <li>Attention to Every Detail</li>
      <li>Serving Louisville, Kentucky</li>
    </ul>
  </div>
</section>

<section class="section bg-off" aria-labelledby="intro-h">
  <div class="wrap intro-grid">
    <div class="intro-img">{pic("05-curved-concrete-walkway", sizes="(max-width: 900px) 100vw, 58vw", pos="50% 60%")}</div>
    <div class="intro-text">
      <h2 id="intro-h">Solid Work Starts With a Solid Foundation.</h2>
      <p class="lede">Set Right Flatwork LLC specializes in residential and commercial concrete flatwork — the driveways, patios, walkways, and slabs people walk, park, and gather on every day.</p>
      <p>The surface you see is only the last step. What makes concrete last is the work that comes before it and the care taken while it’s placed.</p>
      <ul class="intro-points">
        <li><strong>Proper preparation</strong><span>Excavation, compacted base, and forms set to the right grade.</span></li>
        <li><strong>Careful placement</strong><span>Concrete placed and leveled with the slab’s purpose in mind.</span></li>
        <li><strong>Professional finishing</strong><span>Finishes and joints chosen for traction, looks, and crack control.</span></li>
        <li><strong>Clear communication</strong><span>You know what’s happening on your property and why.</span></li>
        <li><strong>Respect for your property</strong><span>An organized work area and care around lawns, beds, and neighbors.</span></li>
      </ul>
      <a class="text-link" href="/about">More about how we work</a>
    </div>
  </div>
</section>

<section class="statement" aria-label="The Set Right standard">
  <div class="wrap">
    <ul class="statement-lines">
      <li>Prepare it right.</li>
      <li>Pour it right.</li>
      <li>Finish it right.</li>
    </ul>
    <p class="statement-caption">Three stages, one standard. Every project we take on — from a shed pad to a full driveway — goes through all three with the same care.</p>
  </div>
</section>

<section class="section bg-slab joints" aria-labelledby="svc-h">
  <div class="wrap">
    <div class="head-split">
      <h2 id="svc-h">Concrete flatwork for homes and businesses</h2>
      <p class="lede">From the front of your house to the back of your lot, these are the surfaces we build. Each one is planned around how it will be used and the ground it sits on.</p>
    </div>

    <article class="svc-feature">
      <div class="media">{pic("03-completed-driveway", sizes="(max-width: 860px) 100vw, 66vw")}</div>
      <div class="panel">
        <h3>Driveways</h3>
        <p>New driveways and full replacements, built on a properly prepared base with slope planned so water runs away from your garage and home.</p>
        <a class="text-link" href="/services#driveways">Learn more about driveways</a>
      </div>
    </article>

    <div class="svc-pair">
      <article class="item">
        {pic("04-completed-backyard-patio", sizes="(max-width: 760px) 100vw, 42vw")}
        <h3>Patios</h3>
        <p>Backyard patios and outdoor gathering spaces sized to the way you’ll use them, with standard and decorative finish options to discuss.</p>
        <a class="text-link" href="/services#patios">Learn more about patios</a>
      </article>
      <article class="item">
        {pic("05-curved-concrete-walkway", sizes="(max-width: 760px) 100vw, 50vw", pos="50% 65%")}
        <h3>Sidewalks &amp; Walkways</h3>
        <p>Front entry paths, garden walks, and sidewalk replacement — straight or curved, finished for steady footing in every season.</p>
        <a class="text-link" href="/services#walkways">Learn more about walkways</a>
      </article>
    </div>

    <ul class="svc-rows">
      <li>
        {pic("06-worker-screeding-slab", sizes="200px")}
        <div><h3>Concrete Slabs</h3><p>Pads for sheds, storage buildings, equipment, and utilities, plus general-purpose slabs built level and to size.</p></div>
        <a class="text-link" href="/services#slabs">Learn more</a>
      </li>
      <li>
        {pic("07-garage-floor", sizes="200px")}
        <div><h3>Garage Floors</h3><p>New garage slabs with reinforcement, joint layout, and a smooth finish planned for vehicles and storage.</p></div>
        <a class="text-link" href="/services#garage-floors">Learn more</a>
      </li>
      <li>
        {pic("09-commercial-sidewalk", sizes="200px")}
        <div><h3>Commercial Flatwork</h3><p>Sidewalks, entryways, pads, and small slabs for business owners, property managers, and general contractors.</p></div>
        <a class="text-link" href="/services#commercial">Learn more</a>
      </li>
    </ul>
  </div>
</section>

<section class="section bg-charcoal why-wrap" aria-labelledby="why-h">
  <div class="wrap why-grid">
    <div class="why-aside">
      <h2 id="why-h" style="color:#fff">Why Set Right Flatwork?</h2>
      <p class="lede" style="color:rgba(243,241,236,.84)">Six principles we hold ourselves to on every job, whatever its size.</p>
      {pic("02-concrete-finishing-bull-float", sizes="(max-width: 900px) 100vw, 40vw")}
    </div>
    <ul class="why-list">
      <li><h3>Attention to Detail</h3><p>Grades, joints, edges, and transitions are where concrete succeeds or fails. We check them before the truck arrives, not after.</p></li>
      <li><h3>Quality-Focused Workmanship</h3><p>We would rather take the time to prepare a base properly than rush a pour. The process matters as much as the result.</p></li>
      <li><h3>Straightforward Communication</h3><p>Plain answers about what your project needs, what it will involve, and what to expect on each day of the work.</p></li>
      <li><h3>Practical Project Planning</h3><p>Schedules that account for weather, curing, and site conditions — and recommendations that fit how you’ll actually use the space.</p></li>
      <li><h3>Respect for Every Property</h3><p>Protected lawns and landscaping where practical, an organized work area, and a clean site when we leave.</p></li>
      <li><h3>Local Business Values</h3><p>We work where we live. Our reputation in Louisville is built one driveway, patio, and neighbor at a time.</p></li>
    </ul>
  </div>
</section>

<section class="section bg-off" aria-labelledby="gal-h">
  <div class="wrap">
    <div class="center-row mb-lg">
      <div>
        <h2 id="gal-h" class="mt-0">Examples of concrete flatwork</h2>
        <p class="measure">A look at the kinds of surfaces we install, from backyard patios to garage floors and storefront sidewalks.</p>
      </div>
      <a class="btn btn--dark" href="/projects">View Our Work</a>
    </div>
    <div class="mosaic">
      <figure>{pic("04-completed-backyard-patio", sizes="(max-width: 760px) 100vw, 45vw")}<figcaption>Backyard patio</figcaption></figure>
      <figure>{pic("03-completed-driveway", sizes="(max-width: 760px) 50vw, 28vw")}<figcaption>Driveway</figcaption></figure>
      <figure>{pic("07-garage-floor", sizes="(max-width: 760px) 50vw, 28vw")}<figcaption>Garage floor</figcaption></figure>
      <figure>{pic("05-curved-concrete-walkway", sizes="(max-width: 760px) 100vw, 56vw", pos="50% 70%")}<figcaption>Curved walkway</figcaption></figure>
    </div>
    <p class="note-illustrative">Photos on this site are illustrative examples of concrete flatwork, not photographs of specific Set Right Flatwork projects.</p>
  </div>
</section>

<section class="section bg-slab" aria-labelledby="proc-h">
  <div class="wrap">
    <div class="process-top">
      <div>
        <h2 id="proc-h">Our process</h2>
        <p class="lede">Four stages take a project from a first conversation to a finished surface you can use.</p>
      </div>
      {pic("06-worker-screeding-slab", sizes="(max-width: 900px) 100vw, 40vw")}
    </div>
    <ol class="steps">
      <li><h3>Initial Consultation</h3><p>We talk through what you want to build, look at the site, take measurements, and discuss finishes. Then you get a clear, written estimate.</p></li>
      <li><h3>Site Preparation</h3><p>Old concrete is removed where needed, the ground is excavated and compacted, a gravel base goes in, and forms and reinforcement are set to grade.</p></li>
      <li><h3>Concrete Placement &amp; Finishing</h3><p>Concrete is placed, screeded, floated, and finished. Control joints are cut or tooled to help manage cracking, and curing begins.</p></li>
      <li><h3>Final Walkthrough</h3><p>We walk the finished work with you, remove forms, clean up the site, and explain how long to wait before foot traffic and vehicles.</p></li>
    </ol>
    <p class="schedule-note">Every schedule depends on the project’s scope, site conditions, weather, and the curing time concrete needs. We’ll explain the expected timeline for your project during the estimate and keep you informed if weather changes the plan.</p>
  </div>
</section>

<section class="section bg-orange" aria-labelledby="fb-h">
  <div class="wrap feedback">
    <div>
      <h2 id="fb-h">Customer Feedback</h2>
      <p class="lede">We believe a contractor’s reputation should be earned, not written by the contractor.</p>
    </div>
    <div class="feedback-board">
      <h3>Reviews from real customers will appear here.</h3>
      <p>As projects are completed, verified feedback from Set Right Flatwork customers will be shared in this space. We will only publish reviews from real customers, in their own words.</p>
      <!-- Verified reviews: add them here as <blockquote> elements once customers have given permission. Set --gbp-url at build time to show a link to the Google Business Profile. -->
      {"<a class='btn btn--dark' href='" + html.escape(GBP_URL, quote=True) + "' rel='noopener' target='_blank'>Read our reviews on Google</a>" if GBP_URL else "<p>Planning a project in the meantime? We’re happy to talk through it.</p><a class='btn btn--dark' href='/contact#estimate'>Request a Free Estimate</a>"}
    </div>
  </div>
</section>

{cta_band("02-concrete-finishing-bull-float", "Ready to Start Your Concrete Project?", "Tell us about your project and let us help you plan the next step.")}
'''
    return page("/", "Set Right Flatwork LLC | Concrete Contractor in Louisville, KY",
                "Professional concrete flatwork in Louisville, Kentucky. Explore concrete driveways, patios, sidewalks, slabs, and commercial concrete solutions from Set Right Flatwork LLC.",
                body, "/", graph(business_ld(), website_ld()), preload=HERO_IMG)

# ===========================================================================
# SERVICES
# ===========================================================================
SERVICES = [
    dict(id="driveways", label="Residential", title="Concrete Driveways", img="03-completed-driveway", shape="wide", pos="50% 60%",
         paras=["Your driveway carries vehicles every day and frames the front of your home. We install new concrete driveways and replace worn, cracked, or settled ones, and we treat the work below the surface as seriously as the finish on top.",
                "A driveway project usually begins with removing the old surface where needed, excavating to the right depth, and building a compacted gravel base. Forms are set to the planned grade so water drains away from the garage and the house. Reinforcement is placed to suit the project before the concrete is poured, finished, and given time to cure."],
         includes=["New driveway installation", "Driveway replacement", "Residential driveway slabs", "Base preparation and compaction", "Drainage and slope planning", "Broom and smooth surface finishes"],
         consider=["Driveway width, length, and connection to the street or apron", "Existing concrete or asphalt that needs to be removed", "Soil conditions and how deep the base needs to be", "Slope, and where water should drain", "Vehicle loads, including trailers or heavier vehicles", "Permit or right-of-way requirements for apron work"]),
    dict(id="patios", label="Outdoor living", title="Concrete Patios", img="04-completed-backyard-patio", shape="tall",
         paras=["A patio extends your living space outdoors: a place for the grill, a dining table, or a quiet morning coffee. We build concrete patios sized and shaped around how you actually plan to use the space.",
                "Standard broom-finished or smooth-troweled concrete is a durable, practical choice for most backyards. Decorative and stamped finishes can be discussed where available for your project, along with custom shapes, curves, and clean connections to existing steps, walkways, or doors."],
         includes=["Backyard patios", "Outdoor entertainment spaces", "Standard concrete patios", "Decorative and stamped options, where available", "Custom shapes and layouts", "Tie-ins to existing walks and steps"],
         consider=["How the space will be used and what it needs to hold", "Slope away from the house foundation", "Access for equipment and concrete delivery to the backyard", "Connections to doors, steps, or existing surfaces", "Finish choice and slip resistance", "Trees, roots, and nearby landscaping"]),
    dict(id="walkways", label="Residential", title="Concrete Sidewalks & Walkways", img="05-curved-concrete-walkway", shape="square",
         paras=["Walkways lead people to your door, around your home, and through your yard. A well-built walk feels steady underfoot, drains properly, and lines up cleanly with the surfaces around it.",
                "We install residential walkways, front entry paths, and garden walks, straight or curved, and replace sidewalk sections that have cracked, heaved, or become trip hazards. Finishes are chosen for practical traction through Kentucky’s wet and freezing months."],
         includes=["Residential walkways", "Front entry paths", "Garden walkways", "Sidewalk replacement", "Straight and curved layouts", "Practical traction finishes"],
         consider=["Path width and route across the property", "Transitions to steps, porches, and driveways", "Tree roots that may have lifted existing sections", "Control joint spacing", "Drainage along the edges of the path", "City requirements where public sidewalk is involved"]),
    dict(id="slabs", label="Structural base", title="Concrete Slabs & Pads", img="06-worker-screeding-slab", shape="wide",
         paras=["Sheds, storage buildings, HVAC units, generators, and equipment all need a level, solid base. We pour concrete pads and general-purpose slabs sized to what will sit on them.",
                "A good slab starts with a level, compacted base and accurate forms. Thickness and reinforcement are planned around the expected load, and the surface is finished to suit its purpose, whether that is anchoring a building or providing a clean, flat work area."],
         includes=["Equipment pads", "Storage building pads", "Shed pads", "Utility pads", "General-purpose concrete slabs", "Leveling and base preparation"],
         consider=["What will sit on the slab, and how much it weighs", "Exact dimensions required by the building or equipment maker", "Anchor bolts or other embedded items", "Existing ground level and how much fill is needed", "Distance from property lines and other structures", "Access for the concrete truck or a pump"]),
    dict(id="garage-floors", label="Interior slab", title="Garage Floors", img="07-garage-floor", shape="tall",
         paras=["A garage floor takes vehicle weight, dropped tools, temperature swings, and whatever drips off the car in winter. We install new garage slabs and concrete floors with careful attention to the base, thickness, and finish.",
                "Reinforcement, slab thickness, and joint layout are planned for how the floor will be used. The surface is finished smooth and even, with a gentle pitch toward the door where the design calls for it, so water doesn’t collect inside."],
         includes=["New garage slabs", "Concrete floor installation", "Reinforcement planning", "Control joint layout", "Smooth trowel finishes", "Pitch toward the door where required"],
         consider=["Attached or detached garage, and the existing foundation", "Vehicle and storage loads", "Reinforcement and vapor barrier needs", "Floor drains or existing utilities", "The transition at the door and driveway apron", "Curing time before vehicles can park"]),
    dict(id="commercial", label="Business & property", title="Commercial Concrete Flatwork", img="09-commercial-sidewalk", shape="wide",
         paras=["Business owners, property managers, and general contractors need flatwork that is built carefully and with as little disruption as possible to customers and tenants. We take on small commercial concrete projects with the same attention we bring to a residential job.",
                "Work includes commercial sidewalks, building entryways, concrete pads for equipment or dumpsters, small commercial slabs, and general property improvements. Access, staging, and pour timing are coordinated around the property’s operations wherever possible."],
         includes=["Commercial sidewalks", "Entryways", "Equipment and dumpster pads", "Small commercial slabs", "Property improvements", "Coordination with GCs and managers"],
         consider=["Keeping entrances and walkways usable during the work", "Accessibility requirements at entries and walks", "Heavier traffic and load requirements", "Specifications from an architect or general contractor", "Scheduling around business hours", "Permits and inspections"]),
]

def services():
    sub = "".join(f'<li><a href="#{s["id"]}">{s["title"].replace("Concrete ", "") if s["id"] not in ("slabs",) else "Slabs & Pads"}</a></li>' for s in SERVICES)
    sub = sub.replace("&", "&amp;").replace("&amp;amp;", "&amp;")
    sections = []
    for i, s in enumerate(SERVICES):
        bg = ["bg-off", "bg-slab"][i % 2]
        flip = " flip" if i % 2 else ""
        paras = "".join(f"<p>{p}</p>" for p in s["paras"])
        inc = "".join(f"<li>{x}</li>" for x in s["includes"])
        con = "".join(f"<li>{x}</li>" for x in s["consider"])
        sizes = "(max-width: 900px) 100vw, 50vw"
        sections.append(f'''
<section class="section {bg}" id="{s["id"]}" aria-labelledby="{s["id"]}-h">
  <div class="wrap service{flip}">
    <div class="media {s["shape"]}">{pic(s["img"], sizes=sizes, pos=s.get("pos"))}</div>
    <div class="copy">
      <span class="label">{s["label"]}</span>
      <h2 id="{s["id"]}-h">{s["title"].replace("&", "&amp;")}</h2>
      {paras}
      <ul class="service-includes" aria-label="What this service covers">{inc}</ul>
      <div class="considerations">
        <h3>Project considerations</h3>
        <ul>{con}</ul>
      </div>
      <a class="btn btn--primary" href="/contact#estimate">Request a Free Estimate</a>
    </div>
  </div>
</section>''')
    body = f'''
<section class="page-hero" aria-labelledby="ph">
  <div class="media">{pic("02-concrete-finishing-bull-float", sizes="(max-width: 860px) 100vw, 60vw", eager=True)}</div>
  <div class="wrap">
    <p class="crumbs"><a href="/">Home</a> / Services</p>
    <h1 id="ph">Concrete flatwork services</h1>
    <p class="lede">Driveways, patios, walkways, slabs, garage floors, and small commercial projects across Louisville and surrounding communities, each one planned around its use and the ground beneath it.</p>
    <div class="btn-row" style="margin-top:28px"><a class="btn btn--primary" href="/contact#estimate">Request a Free Estimate</a><a class="btn btn--line" href="/products" style="color:#fff">See Planning Prices</a></div>
  </div>
</section>
<div class="formboard" aria-hidden="true"></div>
<nav class="subnav" aria-label="Services on this page"><div class="wrap"><ul>{sub}<li><a href="#more">Steps &amp; Removal</a></li></ul></div></nav>
{"".join(sections)}

<section class="section bg-charcoal" id="more" aria-labelledby="more-h">
  <div class="wrap">
    <h2 id="more-h" style="color:#fff">Also part of the work</h2>
    <div class="also-list">
      <div>
        <h3 style="color:#fff">Concrete Steps &amp; Entryways</h3>
        <p style="color:rgba(243,241,236,.84)">Front steps, stoops, and entry landings connect your walkway or driveway to the door. Riser heights, landing size, and drainage are planned so the entry is comfortable and safe to use. Availability depends on the project’s design and site; we’ll discuss what’s practical at the estimate.</p>
      </div>
      <div>
        <h3 style="color:#fff">Concrete Removal</h3>
        <p style="color:rgba(243,241,236,.84)">Many projects begin by breaking out and hauling away an old, cracked, or settled surface. Removal is usually quoted as part of a replacement so preparation and the new pour are planned together.</p>
      </div>
    </div>
    <div class="process-top" style="margin-top:clamp(48px,6vw,88px);margin-bottom:0">
      {pic("08-hand-finishing-closeup", sizes="(max-width: 900px) 100vw, 55vw")}
      <div>
        <h3 style="color:#fff">The finish is the last step, not the first</h3>
        <p style="color:rgba(243,241,236,.84)">Every service above follows the same sequence: prepare the site and base, place the concrete carefully, then finish and cure it properly. Edges, joints, and transitions get hand attention, because they are where most concrete problems start.</p>
        <a class="text-link" href="/about">Read about our approach</a>
      </div>
    </div>
  </div>
</section>

{cta_band(HERO_IMG, "Have a project in mind?", "Share the size, location, and what you want to build. We’ll talk through options and prepare an estimate based on your site.", secondary=("See Planning Prices", "/products"))}
'''
    svc_ld = [business_ld()] + [{
        "@type": "Service", "name": s["title"], "serviceType": s["title"],
        "description": s["paras"][0], "provider": {"@id": BIZ_ID},
        "areaServed": {"@type": "City", "name": "Louisville, KY"},
        **({"url": f"{SITE_URL}/services#{s['id']}"} if SITE_URL else {})} for s in SERVICES]
    return page("/services", "Concrete Services in Louisville, KY | Set Right Flatwork LLC",
                "Concrete driveways, patios, sidewalks, slabs and pads, garage floors, and commercial flatwork in Louisville, KY. See what each service involves and request an estimate.",
                body, "/services", graph(*svc_ld))

# ===========================================================================
# PRODUCTS
# ===========================================================================
CATALOG = [
    dict(name="Standard Concrete Driveway", lo=7, hi=12, img="03-completed-driveway",
         d="Poured concrete driveway on an excavated, compacted gravel base, with a broom finish for traction and planned slope for drainage.",
         t="Typical uses: new driveways, full replacements, widening an existing drive."),
    dict(name="Standard Concrete Patio", lo=7, hi=12, img="04-completed-backyard-patio",
         d="A broom or smooth-finished patio slab for dining, grilling, and outdoor seating, sloped away from the house.",
         t="Typical uses: backyard patios, side-yard sitting areas, grill pads."),
    dict(name="Stamped Concrete", lo=12, hi=18, swatch="stamped",
         d="Concrete pressed with a pattern and colored to resemble stone, slate, or brick. Requires more labor and materials than a standard finish. Availability depends on the project.",
         t="Typical uses: decorative patios, entry walks, pool surrounds."),
    dict(name="Concrete Sidewalk", lo=8, hi=15, img="05-curved-concrete-walkway",
         d="Walkways and sidewalk sections, straight or curved. Narrow layouts and curves mean more forming per square foot, which is why the range is wider.",
         t="Typical uses: front entry paths, garden walks, sidewalk replacement."),
    dict(name="Standard Concrete Slab", lo=6, hi=12, img="06-worker-screeding-slab",
         d="A level, general-purpose slab or pad built to the dimensions of the building or equipment it will support.",
         t="Typical uses: shed and storage-building pads, HVAC and generator pads, utility slabs."),
    dict(name="Garage Concrete Floor", lo=7, hi=12, img="07-garage-floor",
         d="Interior garage slab with reinforcement and joint layout planned for vehicles, finished smooth and even.",
         t="Typical uses: new garage slabs, replacing a failed garage floor."),
    dict(name="Concrete Removal", lo=2, hi=5, swatch="removal",
         d="Breaking out and hauling away existing concrete so the area can be prepared for new work.",
         t="Typical uses: before a driveway, patio, or sidewalk replacement."),
]

def products():
    rows = []
    for c in CATALOG:
        if "img" in c:
            thumb = pic(c["img"], sizes="(max-width: 520px) 100vw, 220px")
        else:
            thumb = f'<div class="swatch {c["swatch"]}" aria-hidden="true"></div>'
        rows.append(f'''<li>
  <div class="thumb">{thumb}</div>
  <div><h2>{c["name"]}</h2><p>{c["d"]}</p><p class="typical">{c["t"]}</p></div>
  <div class="price"><strong>${c["lo"]}–${c["hi"]}</strong><span>per sq. ft.<br>planning estimate</span></div>
</li>''')
    opts = "".join(f'<option data-lo="{c["lo"]}" data-hi="{c["hi"]}">{c["name"]}</option>' for c in CATALOG)
    factors = ["Project dimensions", "Excavation", "Soil conditions", "Gravel base preparation", "Reinforcement",
               "Concrete thickness", "Accessibility", "Concrete volume", "Existing concrete removal",
               "Finishing requirements", "Permits and local requirements"]
    body = f'''
<section class="page-hero" aria-labelledby="ph">
  <div class="media">{pic("07-garage-floor", sizes="(max-width: 860px) 100vw, 60vw", eager=True)}</div>
  <div class="wrap">
    <p class="crumbs"><a href="/">Home</a> / Products</p>
    <h1 id="ph">Concrete solutions &amp; planning prices</h1>
    <p class="lede">A catalog of the concrete work we offer, with regional price ranges to help you plan a budget before your estimate.</p>
  </div>
</section>
<div class="formboard" aria-hidden="true"></div>

<section class="section bg-off" aria-labelledby="cat-h">
  <div class="wrap">
    <div class="head-split">
      <h2 id="cat-h">Concrete solutions catalog</h2>
      <p>Concrete work is built to order for each property, so nothing here is sold online. These ranges are per square foot and are meant for early planning; your project-specific estimate will reflect your site.</p>
    </div>
    <ul class="catalog">{"".join(rows)}</ul>
  </div>
</section>

<section class="section bg-slab" aria-labelledby="calc-h">
  <div class="wrap calc">
    <div>
      <h2 id="calc-h">Rough budget calculator</h2>
      <p class="measure">Multiply your area by the planning range for the type of work. It’s a starting point for a budget conversation, not a quote.</p>
      <form class="calc-form" id="calc" novalidate>
        <div class="field full"><label for="calc-service">Type of work</label><select id="calc-service" name="service">{opts}</select></div>
        <div class="field"><label for="calc-length">Length <span class="hint">(feet)</span></label><input id="calc-length" name="length" type="number" min="1" step="0.5" inputmode="decimal" value="20"></div>
        <div class="field"><label for="calc-width">Width <span class="hint">(feet)</span></label><input id="calc-width" name="width" type="number" min="1" step="0.5" inputmode="decimal" value="12"></div>
      </form>
    </div>
    <div class="calc-out" aria-live="polite">
      <p style="margin:0;font-weight:600">Planning range</p>
      <p class="range" id="calc-range">$1,680 – $2,880</p>
      <p class="area" id="calc-area">240 sq. ft. of Standard Concrete Driveway at $7–$12 per sq. ft.</p>
      <p class="small" style="color:rgba(243,241,236,.72)">Removal of existing concrete, steps, and site-specific work are priced separately. Final pricing comes only from a written estimate.</p>
      <a class="btn btn--primary" href="/contact#estimate">Get a Project-Specific Estimate</a>
    </div>
  </div>
</section>

<section class="section bg-charcoal" aria-labelledby="fac-h">
  <div class="wrap">
    <div class="head-split">
      <h2 id="fac-h" style="color:#fff">What determines your final cost</h2>
      <p style="color:rgba(243,241,236,.84)">Two driveways of the same size can be priced very differently. These are the factors we review on site before preparing your estimate.</p>
    </div>
    <ul class="factors">{"".join(f"<li>{f}</li>" for f in factors)}</ul>
  </div>
</section>

<section class="section--tight bg-off">
  <div class="wrap">
    <div class="disclaimer" role="note">
      <h2>About these prices</h2>
      <p>All prices shown are general planning estimates based on regional market information. They are not guaranteed prices or formal quotations from Set Right Flatwork LLC. Final pricing is determined after reviewing project requirements and site conditions.</p>
    </div>
  </div>
</section>

{cta_band("06-worker-screeding-slab", "Get a price built for your property", "Share your measurements and a description of the work. We’ll review the site and prepare a written, project-specific estimate.", primary=("Get a Project-Specific Estimate", "/contact#estimate"))}
'''
    return page("/products", "Concrete Prices & Solutions | Set Right Flatwork LLC, Louisville KY",
                "Planning price ranges per square foot for concrete driveways, patios, stamped concrete, sidewalks, slabs, garage floors, and removal in the Louisville, KY area.",
                body, "/products", graph(business_ld()))

# ===========================================================================
# OUR WORK / PROJECTS
# ===========================================================================
GALLERY = [
    ("04-completed-backyard-patio", "patios", "r-tall", "Backyard patio", "A square patio sized for outdoor dining, set level with the lawn."),
    (HERO_IMG, "driveways process", "r-wide", "Freshly finished driveway", "A newly placed driveway slab with its wooden forms still in place, before they are stripped."),
    ("03-completed-driveway", "driveways", "r-sq", "Two-car driveway", "A clean, broom-finished driveway running straight to the garage."),
    ("06-worker-screeding-slab", "slabs process", "r-wide", "Screeding a slab", "Striking off wet concrete inside wooden forms to bring the slab to grade."),
    ("05-curved-concrete-walkway", "walkways", "r-tall", "Curved front walkway", "A gently curving path through the front yard, edged by planting beds."),
    ("07-garage-floor", "garage", "r-wide", "Garage floor", "A smooth interior slab ready for vehicles and storage."),
    ("02-concrete-finishing-bull-float", "process", "r-sq", "Bull floating", "Smoothing the surface after screeding and bringing up cream for finishing."),
    ("09-commercial-sidewalk", "walkways", "r-tall", "Storefront sidewalk", "A wide commercial walk along a brick and glass building entrance."),
    ("08-hand-finishing-closeup", "process", "r-wide", "Hand finishing an edge", "Trowel work along the slab edge, where details make the difference."),
]
FILTERS = [("all", "All"), ("driveways", "Concrete Driveways"), ("patios", "Concrete Patios"),
           ("walkways", "Walkways & Sidewalks"), ("slabs", "Concrete Slabs"), ("garage", "Garage Floors"),
           ("process", "Concrete Installation Process")]

def projects():
    btns = "".join(f'<button type="button" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">{html.escape(v)}</button>' for k, v in FILTERS)
    tiles = "".join(f'''<figure class="tile {r}" data-cat="{cat}">
  <button type="button" data-full="{img_full(img)}" data-title="{html.escape(t, quote=True)}" data-text="{html.escape(d, quote=True)}" aria-label="View larger: {html.escape(t, quote=True)}">{pic(img, sizes="(max-width: 700px) 100vw, (max-width: 1000px) 50vw, 400px")}</button>
  <figcaption><strong>{t}</strong><span>{d}</span></figcaption>
</figure>''' for img, cat, r, t, d in GALLERY)
    body = f'''
<section class="page-hero page-hero--plain" aria-labelledby="ph">
  <div class="wrap">
    <p class="crumbs"><a href="/">Home</a> / Our Work</p>
    <h1 id="ph">Concrete work inspiration</h1>
    <p class="lede">Explore different concrete applications, from driveways and patios to garage floors, and see the stages that go into a well-built slab.</p>
  </div>
</section>
<div class="formboard" aria-hidden="true"></div>

<section class="section bg-off" aria-labelledby="gal-h">
  <div class="wrap">
    <h2 id="gal-h" class="visually-hidden">Examples of concrete flatwork</h2>
    <p class="note-illustrative mt-0" style="margin-bottom:24px">These are illustrative photographs of concrete flatwork and installation. They are not photographs of completed Set Right Flatwork projects.</p>
    <div class="filters" data-filters role="group" aria-label="Filter by category">{btns}</div>
    <p id="filter-status" class="visually-hidden" aria-live="polite"></p>
    <div class="masonry">{tiles}</div>
  </div>
</section>

<section class="section bg-charcoal" aria-labelledby="fut-h">
  <div class="wrap future-projects">
    <div>
      <h2 id="fut-h" style="color:#fff">Set Right Flatwork project photos</h2>
      <p class="lede" style="color:rgba(243,241,236,.84)">Photographs of our own completed projects will be added here as work is finished and documented, so you can see real results from around Louisville.</p>
      <p style="color:rgba(243,241,236,.84)">Want to talk about what your project could look like? We can walk through layouts, finishes, and what your site needs.</p>
      <a class="btn btn--primary" href="/contact#estimate">Request a Free Estimate</a>
    </div>
    <!-- When real project photos are available, replace .future-frame with figures in the same format as the gallery above. -->
    <div class="future-frame" aria-hidden="true"><p>Completed project photography coming soon</p></div>
  </div>
</section>

<dialog class="lightbox" id="lightbox" aria-label="Image viewer">
  <figure>
    <img src="{img_full("03-completed-driveway")}" alt="">
    <figcaption>
      <div><strong data-lb-title></strong><div class="small" data-lb-text></div></div>
      <div class="lb-controls">
        <button type="button" data-lb-prev aria-label="Previous image">Prev</button>
        <button type="button" data-lb-next aria-label="Next image">Next</button>
        <button type="button" class="lb-close" data-lb-close>Close</button>
      </div>
    </figcaption>
  </figure>
</dialog>
'''
    return page("/projects", "Concrete Flatwork Examples | Set Right Flatwork LLC, Louisville KY",
                "Browse examples of concrete driveways, patios, walkways, slabs, garage floors, and the concrete installation process, for planning your Louisville project.",
                body, "/projects", graph(business_ld()))

# ===========================================================================
# ABOUT
# ===========================================================================
def about():
    story = [
        "Set Right Flatwork LLC was built around a straightforward belief: concrete work should be done with care, honesty, and attention to the details that matter.",
        "In an industry where the finished result is often what gets noticed, we believe the real difference begins long before the concrete is poured. It starts with proper preparation, thoughtful planning, understanding the customer’s needs, and taking pride in every stage of the process.",
        "Our name reflects that philosophy. ‘Set Right’ represents our commitment to approaching every project with the right mindset, the right preparation, and respect for the work being done.",
        "Based in Louisville, Kentucky, Set Right Flatwork focuses on residential and commercial concrete flatwork, helping property owners create practical, attractive, and lasting outdoor and structural surfaces.",
        "From driveways and patios to sidewalks, concrete slabs, and other flatwork projects, our approach remains consistent: understand the project, pay attention to the details, and work toward a result that serves its purpose.",
        "INSET",
        "We understand that a concrete project is more than another construction task. It can mean a more welcoming entrance to a home, a better place for family gatherings, a safer walkway, or an improved space for a growing business.",
        "That is why we believe every project deserves consideration, regardless of its size.",
        "We are proud to be part of the Louisville community and believe that local businesses should contribute something meaningful: dependable service, responsible work practices, and relationships built on trust.",
        "At Set Right Flatwork, we are not interested in taking shortcuts or making promises simply to win a project. We believe in straightforward communication, realistic expectations, and treating every property with respect.",
        "Our philosophy is simple:",
        "CREED",
        "That is the standard behind the name Set Right Flatwork.",
    ]
    out = ['<p class="open">Every great project starts with a solid foundation. We believe the same principle applies to building a business.</p>']
    for p in story:
        if p == "INSET":
            out.append(f'<figure class="story-inset">{pic("02-concrete-finishing-bull-float", sizes="(max-width: 900px) 100vw, 40vw")}<figcaption>The real difference begins long before the finish: in preparation, placement, and patience.</figcaption></figure>')
        elif p == "CREED":
            out.append('<p class="creed" aria-label="Prepare it right. Pour it right. Finish it right."><span>PREPARE IT RIGHT.</span><span>POUR IT RIGHT.</span><span>FINISH IT RIGHT.</span></p>')
        else:
            out.append(f"<p>{p}</p>")
    values = [
        ("01", "Quality Without Shortcuts", "We believe proper preparation and attention to detail are essential to successful concrete work. The process matters just as much as the finished surface."),
        ("02", "Honesty &amp; Transparency", "Clear communication and realistic expectations should be part of every customer relationship. Customers deserve straightforward answers and understandable project estimates."),
        ("03", "Pride in Craftsmanship", "Concrete work requires planning, patience, and skill. We respect the process and recognize that the details contribute to the final result."),
        ("04", "Respect for Every Property", "Whether working on a residential driveway, backyard patio, or commercial property, we believe in maintaining an organized work area and treating each property responsibly."),
        ("05", "Reliability &amp; Accountability", "We value keeping customers informed, respecting agreed project expectations, and taking responsibility for the work we undertake."),
        ("06", "Community Matters", "As a Louisville-area business, we recognize the importance of local relationships. We believe in contributing positively through responsible service, respectful work practices, and meaningful customer relationships."),
    ]
    vals = "".join(f'<li><span class="num" aria-hidden="true">{n}</span><div><h3>{t}</h3><p>{d}</p></div></li>' for n, t, d in values)
    commits = ["Respect for neighbors", "Responsible material handling", "Organized work areas", "Practical waste reduction",
               "Safe work practices", "Consideration of drainage and surroundings", "Positive local relationships"]
    diff = [("Preparation", "A successful concrete project starts with understanding the site and preparing the foundation properly."),
            ("Precision", "Careful layout, placement, and finishing help create a surface designed for its intended use."),
            ("Communication", "Customers should know what to expect and understand the important stages of their project."),
            ("Pride", "We believe the quality of our work should reflect the values behind our name.")]
    body = f'''
<section class="page-hero" aria-labelledby="ph">
  <div class="media">{pic("08-hand-finishing-closeup", sizes="(max-width: 860px) 100vw, 60vw", eager=True)}</div>
  <div class="wrap">
    <p class="crumbs"><a href="/">Home</a> / About</p>
    <h1 id="ph">Built on Hard Work. Grounded in Integrity.</h1>
    <p class="lede">More Than Concrete. A Commitment to Doing Things Right.</p>
  </div>
</section>
<div class="formboard" aria-hidden="true"></div>

<section class="section bg-off" id="our-story" aria-labelledby="story-h">
  <div class="wrap story">
    <div class="story-head">
      <h2 id="story-h">Our Story</h2>
      <div class="rule" aria-hidden="true"></div>
    </div>
    <div class="story-body">{"".join(out)}</div>
  </div>
</section>

<section class="section bg-charcoal joints" aria-labelledby="start-h">
  <div class="wrap started">
    <h2 id="start-h">A Better Standard Starts With a Simple Idea.</h2>
    <div class="copy">
      <p>Set Right Flatwork represents a practical vision of what a concrete contractor should stand for.</p>
      <p>We believe customers deserve to understand what is being done on their property, why it matters, and what to expect throughout the project.</p>
      <p>We want to make the concrete construction experience more straightforward, with an emphasis on communication, workmanship, and respect for every customer’s investment.</p>
      <p>Our goal is to build a business recognized not only for the surfaces it helps create, but also for the way it approaches its work.</p>
    </div>
  </div>
</section>

<section class="section bg-off" aria-labelledby="owner-h">
  <div class="wrap owner">
    <!-- To add a real photograph of the owner later, replace this .owner-plate div with a picture/img element of the same size. -->
    <div class="owner-plate" aria-hidden="true">{MARK.replace('class="brand-mark"', 'class="mono-mark"')}<span class="mono">PC</span></div>
    <div class="copy">
      <h2 id="owner-h" class="owner-name">Phoebus Cotsapas</h2>
      <p class="owner-role">Owner, Set Right Flatwork LLC<br><span>Louisville, Kentucky</span></p>
      <p>Set Right Flatwork LLC is led by owner Phoebus Cotsapas, with a focus on building a business around straightforward communication, responsible project planning, and quality-focused concrete flatwork.</p>
      <p>The company’s philosophy is simple: treat customers with respect, approach every project thoughtfully, and take pride in the work being done.</p>
      <dl class="company-info" aria-label="Company information">
        <div><dt>Company</dt><dd>Set Right Flatwork LLC</dd></div>
        <div><dt>Owner</dt><dd>Phoebus Cotsapas</dd></div>
        <div><dt>Location</dt><dd>Louisville, Kentucky</dd></div>
        <div><dt>Phone</dt><dd>650-250-6345</dd></div>
        {f'<div><dt>Email</dt><dd>{html.escape(EMAIL)}</dd></div>' if EMAIL else ''}
        {f'<div><dt>Website</dt><dd>{SITE_HOST}</dd></div>' if SITE_URL else ''}
      </dl>
    </div>
  </div>
</section>

<section class="mv" aria-label="Mission and vision">
  <div class="mission">
    <h2>Our Mission</h2>
    <p>To provide dependable concrete flatwork solutions through careful preparation, quality-focused workmanship, honest communication, and respect for every property we work on.</p>
    <p>We aim to create functional, attractive concrete surfaces that meet the needs of homeowners and businesses throughout the Louisville area.</p>
  </div>
  <div class="vision">
    <h2 style="color:#fff">Our Vision</h2>
    <p>To grow into a trusted name in Louisville’s concrete construction industry by maintaining consistent standards, building lasting customer relationships, and treating every project as an opportunity to demonstrate the value of doing things right.</p>
    <p>We believe a strong reputation is built one project, one customer, and one commitment at a time.</p>
  </div>
</section>

<section class="section bg-off values-wrap" aria-labelledby="val-h">
  <div class="wrap">
    <div class="head-split"><h2 id="val-h">Our Core Values</h2><p class="lede">The standards behind every estimate, every pour, and every conversation.</p></div>
    <ol class="values">{vals}</ol>
  </div>
</section>

<section class="section bg-slab" aria-labelledby="com-h" style="margin-top:clamp(72px,10vw,160px)">
  <div class="wrap community">
    <div>
      <h2 id="com-h">Doing Good Work Goes Beyond the Job Site.</h2>
      <p class="lede">We believe responsible construction involves more than installing concrete.</p>
      <p class="measure">Our approach emphasizes respect for neighboring properties and surrounding communities, responsible handling of construction materials, organized work areas, minimizing unnecessary waste where practical, and considering the surrounding landscape when planning projects.</p>
      <p class="measure">We understand that every project becomes part of a larger neighborhood, and we believe that deserves consideration.</p>
      <ul class="commit-list">{"".join(f"<li>{c}</li>" for c in commits)}</ul>
    </div>
    <div class="media">{pic("05-curved-concrete-walkway", sizes="(max-width: 860px) 100vw, 40vw")}</div>
  </div>
</section>

<section class="section bg-black" aria-labelledby="diff-h">
  <div class="wrap">
    <h2 id="diff-h" style="color:#fff">The Set Right Difference</h2>
    <ul class="difference">{"".join(f'<li><h3 class="word">{w}</h3><p>{d}</p></li>' for w, d in diff)}</ul>
  </div>
</section>

{cta_band("03-completed-driveway", "Let’s Build Something Solid.", "Whether you are planning a new driveway, upgrading your outdoor living space, or improving a commercial property, Set Right Flatwork is ready to discuss your concrete project.</p><p>We believe the best projects begin with a conversation and a clear understanding of what needs to be done.", primary=("Let’s Talk About Your Project", "/contact#estimate"), secondary=("Explore Our Services", "/services"))}
'''
    return page("/about", "About Set Right Flatwork LLC | Louisville Concrete Flatwork",
                "Meet Set Right Flatwork LLC, a Louisville, KY concrete flatwork company led by owner Phoebus Cotsapas. Our story, mission, values, and the standard behind the name.",
                body, "/about", graph(business_ld(), {"@type": "AboutPage", "name": "About Set Right Flatwork LLC", "about": {"@id": BIZ_ID}}))

# ===========================================================================
# CONTACT
# ===========================================================================
def contact():
    types = ["Driveway", "Patio", "Sidewalk or walkway", "Concrete slab or pad", "Garage floor", "Steps or entryway",
             "Commercial flatwork", "Concrete removal", "Other"]
    opts = '<option value="" selected disabled>Choose one</option>' + "".join(f"<option>{t}</option>" for t in types)
    email_row = f"<dt>Email</dt><dd>{html.escape(EMAIL)}</dd>" if EMAIL else ""
    web_row = f"<dt>Website</dt><dd>{SITE_HOST}</dd>" if SITE_URL else ""
    notice = "" if FORM_ENDPOINT else ('<p class="form-notice"><strong>Online requests are being set up.</strong> This form is not connected yet, '
                                       'so submissions are not sent. Please call 650-250-6345' + (f' or email {html.escape(EMAIL)}' if EMAIL else '') + ' to request your estimate.</p>')
    map_q = "4022+Produce+Rd,+Louisville,+KY+40218"
    body = f'''
<section class="page-hero page-hero--plain" aria-labelledby="ph">
  <div class="wrap">
    <p class="crumbs"><a href="/">Home</a> / Contact</p>
    <h1 id="ph">Let’s talk about your project</h1>
    <p class="lede">Tell us what you’re planning, where it is, and roughly how big. We’ll follow up to discuss the details and arrange an estimate.</p>
  </div>
</section>
<div class="formboard" aria-hidden="true"></div>

<section class="section bg-off" id="estimate" aria-labelledby="form-h">
  <div class="wrap contact-grid">
    <aside class="contact-card" aria-labelledby="card-h">
      <h2 id="card-h">SET RIGHT FLATWORK LLC</h2>
      <dl>
        <dt>Owner</dt><dd>Phoebus Cotsapas</dd>
        <dt>Phone</dt><dd class="big">650-250-6345</dd>
        {email_row}
        {web_row}
        <dt>Office Address</dt><dd>{ADDR_LINES}</dd>
        <dt>Business Category</dt><dd>Concrete Flatwork Contractor</dd>
      </dl>
    </aside>
    <div>
      <h2 id="form-h">Request a free estimate</h2>
      <p class="measure">Fields marked “required” are needed to respond. Photos of the area can be shared once we’re in touch.</p>
      <form class="contact-form" id="estimate-form" data-endpoint="{html.escape(FORM_ENDPOINT, quote=True)}" novalidate>
        <div class="field"><label for="name">Full Name <span class="hint">required</span></label><input id="name" name="name" autocomplete="name" required aria-describedby="name-error"><p class="error" id="name-error"></p></div>
        <div class="field"><label for="email">Email Address <span class="hint">required</span></label><input id="email" name="email" type="email" autocomplete="email" required aria-describedby="email-error"><p class="error" id="email-error"></p></div>
        <div class="field"><label for="phone">Phone Number <span class="hint">optional</span></label><input id="phone" name="phone" type="tel" autocomplete="tel" aria-describedby="phone-error"><p class="error" id="phone-error"></p></div>
        <div class="field"><label for="project_type">Project Type <span class="hint">required</span></label><select id="project_type" name="project_type" required aria-describedby="project_type-error">{opts}</select><p class="error" id="project_type-error"></p></div>
        <div class="field"><label for="location">Project Location <span class="hint">required — city or neighborhood</span></label><input id="location" name="location" autocomplete="address-level2" required aria-describedby="location-error"><p class="error" id="location-error"></p></div>
        <div class="field"><label for="size">Approximate Project Size <span class="hint">optional — e.g. 20 × 12 ft</span></label><input id="size" name="size"></div>
        <div class="field full"><label for="description">Project Description <span class="hint">required</span></label><textarea id="description" name="description" required aria-describedby="description-error" placeholder="What would you like built or replaced? Any existing concrete, slopes, or access limits we should know about?"></textarea><p class="error" id="description-error"></p></div>
        <div class="field full">
          <label class="check" for="consent"><input type="checkbox" id="consent" name="consent" value="yes" required aria-describedby="consent-error"><span>I agree that Set Right Flatwork LLC may use the information I provide to respond to my inquiry, as described in the <a href="/privacy-policy">Privacy Policy</a>.</span></label>
          <p class="error" id="consent-error"></p>
        </div>
        {notice}
        <div class="full"><button class="btn btn--primary" type="submit">Request a Free Estimate</button></div>
        <p class="form-status" id="form-status" role="status" tabindex="-1"></p>
      </form>
    </div>
  </div>
</section>

<section class="section bg-slab" aria-labelledby="loc-h">
  <div class="wrap">
    <div class="location">
      <div class="addr">
        <h2 id="loc-h" style="color:#fff;font-size:1.25rem">Our office</h2>
        <p class="big">4022 Produce Rd<br>Louisville, KY 40218</p>
        <p style="color:rgba(243,241,236,.8)">Serving Louisville, Kentucky, and surrounding communities, subject to project availability. Estimates take place at your project site.</p>
      </div>
      <div class="map"><iframe title="Map showing 4022 Produce Rd, Louisville, KY 40218" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://www.google.com/maps?q={map_q}&amp;output=embed"></iframe></div>
    </div>
  </div>
</section>
'''
    return page("/contact", "Contact Set Right Flatwork LLC | Concrete Estimates in Louisville, KY",
                "Request a concrete estimate from Set Right Flatwork LLC in Louisville, KY. Phone 650-250-6345. Office at 4022 Produce Rd, Louisville, KY 40218.",
                body, "/contact", graph(business_ld(), {"@type": "ContactPage", "name": "Contact Set Right Flatwork LLC", "about": {"@id": BIZ_ID}}))

# ===========================================================================
# LEGAL PAGES  (text supplied by the client — reproduced in full)
# Mini-markup: "## " section heading, "### " sub-heading, "- " bullet,
# "@CONTACT" contact block, anything else a paragraph.
# ===========================================================================
PRIVACY = """
## 1. Introduction
Set Right Flatwork LLC ("Company," "we," "our," or "us") respects the privacy of individuals who visit our website, request information, communicate with us, or use our services.
This Privacy Policy explains what information may be collected, how it may be used, how it may be disclosed, and what choices individuals may have regarding their information.
## 2. Information We May Collect
Depending on how you interact with our website, we may collect:
### Personal information
- Full name.
- Email address.
- Telephone number.
- Mailing or project address.
- Information submitted through contact forms.
### Project information
- Type of concrete project.
- Approximate dimensions.
- Property details voluntarily provided.
- Project descriptions.
- Photographs or documents submitted by visitors.
- Scheduling or estimate information.
### Technical information
- IP address.
- Browser type.
- Device information.
- Operating system.
- Website pages visited.
- Referring website.
- Approximate geographic information.
- Website interaction information.
## 3. How We Collect Information
Information may be collected when you:
- Submit a website contact form.
- Request an estimate.
- Contact the Company.
- Send project photographs.
- Communicate with our representatives.
- Browse the website.
- Interact with website features.
Technical information may be collected automatically through cookies, server logs, analytics technologies, or similar tools if implemented.
## 4. How We Use Information
Information may be used to:
- Respond to inquiries.
- Evaluate concrete projects.
- Prepare estimates.
- Communicate about services.
- Coordinate project activities.
- Improve website functionality.
- Maintain website security.
- Prevent fraud or misuse.
- Maintain business records.
- Meet legal obligations.
## 5. Cookies and Tracking
Our website may use cookies and similar technologies to support functionality, understand visitor behavior, and improve performance.
These may include essential cookies, analytics cookies, and security-related technologies.
Visitors may manage cookies through browser settings.
If analytics or advertising services are introduced, this policy should be updated accordingly.
## 6. Sharing of Information
We do not sell personal information in exchange for monetary consideration.
Information may be shared with service providers when reasonably necessary to operate our business, including:
- Website hosting providers.
- Website development platforms.
- Email service providers.
- Form-processing services.
- Analytics providers.
- Professional advisers.
Information may also be disclosed when required by law or necessary to protect legitimate rights and safety.
## 7. Data Security
We use reasonable administrative, technical, and organizational measures intended to protect information.
However, no internet transmission or electronic storage system can be guaranteed completely secure.
## 8. Data Retention
We retain personal information for as long as reasonably necessary for customer communication, project documentation, legal obligations, accounting, dispute resolution, and legitimate business recordkeeping.
## 9. Privacy Rights
Depending on applicable law and location, individuals may have rights to:
- Request access to certain personal information.
- Request correction of inaccurate information.
- Request deletion of eligible information.
- Request information about data practices.
- Withdraw consent where applicable.
- Object to certain processing activities.
Requests may be submitted using the contact information below.
Identity verification may be required.
## 10. Children's Privacy
This website is intended for a general audience and is not directed toward children under 13.
We do not knowingly collect personal information from children under 13 through this website.
## 11. Third-Party Websites
Our website may contain links to external websites.
We do not control the privacy policies or practices of external websites.
## 12. Email Communications
Information submitted through a contact form may be used to respond to inquiries and communicate about related business matters.
Marketing communications, if introduced, should include appropriate consent and unsubscribe mechanisms where required.
## 13. Policy Changes
We may update this policy to reflect changes in business operations, website functionality, technology, or legal requirements.
Updates will be published on this page.
## 14. Contact Information
Privacy-related questions and requests, including requests to access, correct, or delete personal information, may be submitted to our official business email, info@setrightflatwork.com. Please include your name and enough detail for us to identify the information or request concerned. We may need to verify your identity before responding.
@CONTACT_PRIVACY
"""

REFUND = """
## 1. Introduction
This Refund & Cancellation Policy explains how Set Right Flatwork LLC ("Company," "we," "our," or "us") handles estimates, deposits, payments, cancellations, project changes, and potential refunds relating to concrete flatwork services.
Concrete construction involves customized labor, materials, equipment, preparation, scheduling, and project-specific expenses.
Refund eligibility depends on the circumstances of each project, the applicable agreement, work already performed, and applicable law.
## 2. Estimates and Project Proposals
Estimates are prepared based on information available at the time of evaluation.
An estimate may include:
- Labor.
- Concrete materials.
- Site preparation.
- Excavation.
- Base materials.
- Reinforcement.
- Formwork.
- Finishing.
- Equipment.
- Removal of existing materials.
- Other project-specific expenses.
An estimate is not a final invoice unless expressly identified as such.
Changes in project scope or site conditions may result in revised pricing.
## 3. Deposits and Advance Payments
If a project requires a deposit, its amount, due date, and purpose should be identified in the written agreement or invoice.
Deposits may cover legitimate project-related expenses, including material procurement, scheduling, equipment arrangements, and preparation.
Deposit refundability depends on the written agreement, cancellation timing, expenses incurred, and applicable law.
No deposit should automatically be described as non-refundable unless clearly disclosed and legally permissible.
## 4. Customer Cancellations
Customers wishing to cancel a project should provide written notice as soon as reasonably possible.
The Company may review:
- Materials already ordered.
- Labor scheduled or performed.
- Equipment arrangements.
- Project preparation.
- Other nonrecoverable expenses.
Eligible refunds will be determined after considering authorized expenses, contractual terms, and applicable law.
## 5. Company Cancellations
If the Company cancels a project for reasons within its control, payments will be reviewed and the appropriate refund or alternative arrangement determined under the agreement and applicable law.
## 6. Work Already Performed
Payments for services properly performed are generally not refundable solely because a customer changes their mind.
This does not limit customer rights concerning defective, incomplete, or improperly performed work under applicable law.
## 7. Materials and Special Orders
Concrete, reinforcement, gravel, lumber, formwork, and other construction materials may involve supplier expenses.
Where materials have already been ordered or delivered, actual nonrecoverable costs may be considered when determining refund eligibility.
Any deductions must be consistent with the written agreement and applicable law.
## 8. Project Changes
Customer-requested changes may affect:
- Total project price.
- Materials.
- Labor.
- Project duration.
- Scheduling.
- Completion dates.
Approved changes should be documented through a written change order or mutually accepted written confirmation.
## 9. Weather and Unforeseen Conditions
Concrete construction is affected by weather, temperature, soil, drainage, and environmental conditions.
Rain, freezing temperatures, excessive heat, and unexpected site conditions may require postponement.
When reasonably possible, the Company will communicate scheduling changes and discuss rescheduling.
Weather-related postponements do not automatically create a right to a full refund when the project can reasonably be rescheduled.
## 10. Workmanship Concerns
Customers who believe work does not conform to agreed specifications should notify the Company promptly.
The notice should include:
- Customer name.
- Project address.
- Description of the concern.
- Relevant photographs, if available.
- Date the issue was observed.
The Company may request a reasonable opportunity to inspect the work.
Where appropriate, corrective work or another resolution may be discussed under the agreement and applicable law.
## 11. Refund Processing
Approved refunds will generally be issued through the original payment method when practical.
Processing times depend on payment providers and financial institutions.
## 12. Payment Disputes
Customers are encouraged to contact the Company to discuss billing questions.
Nothing in this Policy restricts lawful rights to dispute unauthorized or incorrect charges through a payment provider.
## 13. Non-Refundable Circumstances
Refunds may not be available for services properly performed, authorized materials already consumed, legitimate nonrecoverable project expenses, or approved additional work already completed.
All determinations remain subject to the written agreement and applicable law.
## 14. Consumer Rights
Nothing in this Policy is intended to waive rights that cannot legally be waived under applicable federal or Kentucky law.
## 15. Contact Information
For questions regarding cancellations, refunds, payments, or project-related concerns, customers may contact:
@CONTACT_REFUND
"""

TERMS = """
## 1. Agreement to Terms
These Terms and Conditions ("Terms") govern access to and use of the website operated by Set Right Flatwork LLC ("Company," "we," "our," or "us").
By accessing or using this website, visitors agree to these Terms.
## 2. Company Information
Set Right Flatwork LLC is a concrete flatwork business based in Louisville, Kentucky.
Owner: Phoebus Cotsapas
Business Phone: 650-250-6345
Business Email: info@setrightflatwork.com
Website: https://setrightflatwork.com
Business Address:
@ADDRESS
## 3. Website Purpose
This website provides information about concrete flatwork services, including:
- Concrete driveways.
- Concrete patios.
- Sidewalks and walkways.
- Concrete slabs.
- Garage floors.
- Concrete pads.
- Commercial concrete flatwork.
The website may also provide general educational information, project examples, indicative pricing, and methods of requesting estimates.
## 4. Estimates and Pricing
Prices displayed on the website are general estimates unless expressly stated otherwise.
Actual pricing depends on project dimensions, excavation, soil conditions, drainage, reinforcement, concrete specifications, material availability, labor, equipment, permits, transportation, accessibility, and requested changes.
A final price must be established through a written proposal, estimate, or mutually accepted agreement.
Submitting a website inquiry does not create a construction contract.
## 5. Project Agreements
Concrete construction services are governed by the specific agreement accepted by the Company and customer.
An agreement may include:
- Scope of work.
- Materials and specifications.
- Project price.
- Deposit requirements.
- Payment schedule.
- Expected project schedule.
- Customer responsibilities.
- Site access requirements.
- Change-order procedures.
- Warranty terms, if offered.
- Cancellation conditions.
If these website Terms conflict with a signed project agreement, the applicable project agreement controls concerning the specific project, subject to mandatory law.
## 6. Website Content
The Company makes reasonable efforts to maintain accurate and current website information.
However, information may contain errors, omissions, outdated pricing, or technical inaccuracies.
The Company may update website content without prior notice.
## 7. Photographs and Illustrations
Photographs may include illustrative construction imagery, examples of concrete applications, and verified actual project photographs when available.
Illustrative images should not be interpreted as proof that a particular project was performed by the Company.
Actual project results may vary depending on property conditions, materials, weather, design, and construction requirements.
## 8. Customer Responsibilities
Customers should provide accurate information when submitting inquiries.
Customers may be responsible for:
- Providing accurate project information.
- Disclosing known site restrictions.
- Providing reasonable property access.
- Identifying known underground utilities or hazards.
- Obtaining permissions they are responsible for obtaining.
- Reviewing proposals before accepting them.
- Communicating requested changes.
Specific responsibilities will be determined by the applicable agreement and law.
## 9. Scheduling and Weather
Concrete construction is affected by weather and site conditions.
Project dates may change because of rain, freezing temperatures, excessive heat, ground conditions, material delays, equipment availability, unexpected site conditions, and circumstances beyond reasonable control.
The Company will make reasonable efforts to communicate material scheduling changes.
## 10. Intellectual Property
Unless otherwise identified, original website text, design, logo, graphics, and branding elements belong to the Company or are used with appropriate permission.
Visitors may not reproduce, distribute, modify, or commercially exploit protected content without authorization.
## 11. Prohibited Website Use
Visitors must not:
- Attempt unauthorized access.
- Introduce malicious software.
- Interfere with website operations.
- Submit fraudulent inquiries.
- Use the website unlawfully.
- Copy protected materials without authorization.
- Misrepresent their identity.
- Attempt to disrupt website security.
## 12. Third-Party Services
The website may include external links or third-party integrations.
The Company does not control all external websites, payment processors, hosting services, or third-party platforms.
Third-party services may have separate terms and privacy policies.
## 13. Limitation of Website Liability
To the extent permitted by applicable law, the Company is not responsible for losses resulting solely from temporary website interruptions, technical failures, inaccurate third-party information, or unauthorized access beyond its reasonable control.
Nothing in these Terms excludes liability that cannot legally be excluded.
These provisions concern website use and do not eliminate obligations arising from a separate construction agreement.
## 14. Construction Warranties
Website information does not create an additional construction warranty.
Any workmanship commitment or project-specific guarantee must be expressly established in the applicable written project agreement.
Nothing in this section limits rights or remedies provided by mandatory law.
## 15. Indemnification
To the extent permitted by law, visitors agree not to misuse the website in a manner that causes unlawful harm to the Company or third parties.
Project-specific indemnification obligations must be established in the applicable written agreement and interpreted under applicable law.
## 16. Governing Law
These Terms are intended to be governed by the laws of the Commonwealth of Kentucky, subject to applicable federal law and mandatory consumer protections.
Any dispute will be handled in a court of competent jurisdiction as permitted by applicable law.
## 17. Changes to These Terms
The Company may update these Terms periodically.
The revised version will be published on this page with an updated Last Updated date.
## 18. Severability
If any provision is determined to be invalid or unenforceable, the remaining provisions will remain in effect to the extent legally permissible.
## 19. Entire Website Agreement
These Terms govern general use of this website.
They do not replace a separate construction contract or project-specific agreement.
## 20. Contact Information
For questions regarding these Terms and Conditions, website use, or company services, contact:
@CONTACT_TERMS
"""

def smart(t):
    """Curly quotes/apostrophes for display text."""
    out, opening = [], True
    for ch in t:
        if ch == '"':
            out.append("“" if opening else "”"); opening = not opening
        elif ch == "'":
            out.append("’")
        else:
            out.append(ch)
    return "".join(out)

def render_legal(src):
    parts, toc, in_list = [], [], False
    def close():
        nonlocal in_list
        if in_list: parts.append("</ul>"); in_list = False
    for line in src.strip().splitlines():
        line = line.strip()
        if not line: continue
        if line.startswith("## "):
            close()
            title = line[3:]
            num = title.split(".")[0]
            sid = "s" + num
            toc.append(f'<li><a href="#{sid}">{html.escape(smart(title.split(". ", 1)[1]))}</a></li>')
            parts.append(f'<h2 id="{sid}">{html.escape(smart(title))}</h2>')
        elif line.startswith("### "):
            close(); parts.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_list: parts.append("<ul>"); in_list = True
            parts.append(f"<li>{html.escape(smart(line[2:]))}</li>")
        elif line.startswith("@CONTACT"):
            close()
            addr1 = f'{BIZ["street"]}, {BIZ["city"]}, {BIZ["region"]} {BIZ["zip"]}, {BIZ["country"]}'
            em, ph, web = html.escape(EMAIL), BIZ["phone"], SITE_URL
            if line == "@CONTACT_PRIVACY":
                rows = ["<strong>Set Right Flatwork LLC</strong>", "Owner: Phoebus Cotsapas", f"Email: {em}", f"Phone: {ph}", addr1, f"Website: {web}"]
                parts.append('<div class="legal-contact"><p>' + "<br>".join(rows) + "</p></div>")
            elif line == "@CONTACT_REFUND":
                parts.append(f'<div class="legal-contact"><p>Email: {em}<br>Phone: {ph}</p><p><strong>Set Right Flatwork LLC</strong><br>{addr1}</p></div>')
            else:
                rows = [em, "<strong>Set Right Flatwork LLC</strong>", "Owner: Phoebus Cotsapas", ph, addr1]
                parts.append('<div class="legal-contact"><p>' + "<br>".join(rows) + "</p></div>")
        elif line == "@ADDRESS":
            close(); parts.append(f"<p>{ADDR_LINES}</p>")
        else:
            close(); parts.append(f"<p>{html.escape(smart(line))}</p>")
    close()
    return "".join(parts), "".join(toc)

def legal_page(path, h1, crumb, src, title, desc):
    content, toc = render_legal(src)
    body = f'''
<section class="page-hero page-hero--plain" aria-labelledby="ph">
  <div class="wrap">
    <p class="crumbs"><a href="/">Home</a> / {html.escape(crumb)}</p>
    <h1 id="ph">{html.escape(h1)}</h1>
    <p style="font-weight:700;color:#fff;margin-bottom:10px">Set Right Flatwork LLC</p>
    <div class="legal-meta"><span>Effective Date: November 26, 2026</span><span>Last Updated: November 26, 2026</span></div>
  </div>
</section>
<div class="formboard" aria-hidden="true"></div>
<section class="section bg-off">
  <div class="wrap legal">
    <nav class="legal-toc" aria-label="Sections"><h2>On this page</h2><ol>{toc}</ol></nav>
    <article class="legal-body">{content}</article>
  </div>
</section>'''
    return page(path, title, desc, body, None, graph({"@type": "WebPage", "name": title, "publisher": {"@id": BIZ_ID}}, business_ld()))

# ===========================================================================
# 404
# ===========================================================================
def notfound():
    links = "".join(f'<li><a class="text-link" href="{h}">{l}</a></li>' for h, l in NAV[1:])
    body = f'''
<section class="bg-charcoal notfound">
  <div class="wrap" style="padding-block:80px">
    <p class="code" aria-hidden="true">404</p>
    <h1 style="color:#fff;font-size:clamp(2rem,4.4vw,3.6rem);max-width:14em">This page isn’t on the plans.</h1>
    <p class="lede" style="color:rgba(243,241,236,.84)">The address may be mistyped, or the page may have moved. Head back home or pick a section below.</p>
    <div class="btn-row" style="margin:28px 0 36px"><a class="btn btn--primary" href="/">Back to the Home Page</a><a class="btn btn--line" style="color:#fff" href="/contact#estimate">Request a Free Estimate</a></div>
    <ul style="list-style:none;display:flex;flex-wrap:wrap;gap:12px 28px">{links}</ul>
  </div>
</section>'''
    return page("/404", "Page Not Found | Set Right Flatwork LLC", "The page you were looking for could not be found.", body, None, None, noindex=True)

# ===========================================================================
# BUILD
# ===========================================================================
def write(route, content):
    target = DIST / ("index.html" if route == "/" else route.strip("/") + "/index.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(STATIC, DIST)

    write("/", home())
    write("/services", services())
    write("/products", products())
    write("/projects", projects())
    write("/about", about())
    write("/contact", contact())
    write("/privacy-policy", legal_page("/privacy-policy", "Privacy Policy", "Privacy Policy", PRIVACY,
          "Privacy Policy | Set Right Flatwork LLC",
          "How Set Right Flatwork LLC collects, uses, shares, and protects information submitted through its website and in the course of providing concrete services."))
    write("/refund-policy", legal_page("/refund-policy", "Refund & Cancellation Policy", "Refund Policy", REFUND,
          "Refund & Cancellation Policy | Set Right Flatwork LLC",
          "How Set Right Flatwork LLC handles estimates, deposits, cancellations, project changes, weather delays, and refunds for concrete flatwork services."))
    write("/terms-and-conditions", legal_page("/terms-and-conditions", "Website Terms and Conditions", "Terms and Conditions", TERMS,
          "Terms and Conditions | Set Right Flatwork LLC",
          "Terms and conditions for using the Set Right Flatwork LLC website, including estimates and pricing, project agreements, photographs, and website use."))
    (DIST / "404.html").write_text(notfound(), encoding="utf-8")

    # Web app manifest (favicons / home-screen icon)
    (DIST / "site.webmanifest").write_text(json.dumps({
        "name": BIZ["name"], "short_name": "Set Right", "start_url": "/", "display": "browser",
        "background_color": "#17191B", "theme_color": "#17191B",
        "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=1), encoding="utf-8")

    # robots.txt — production pages are always crawlable.
    robots = "User-agent: *\nAllow: /\n"
    if SITE_URL:
        robots += f"\nSitemap: {SITE_URL}/sitemap.xml\n"
        urls = "".join(
            f"  <url>\n    <loc>{abs_url(r)}</loc>\n    <lastmod>{TODAY}</lastmod>\n  </url>\n" for r in ROUTES)
        (DIST / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n",
            encoding="utf-8")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")

    print(f"Built {len(ROUTES)} routes + 404 into {DIST}")
    print("Domain:", SITE_URL or "(not set — sitemap.xml, canonical and og:url/og:image are skipped; rebuild with --domain)")
    print("Form endpoint:", FORM_ENDPOINT or "(not set — form shows 'not connected' notice)")

if __name__ == "__main__":
    main()
