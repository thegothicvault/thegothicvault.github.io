# -*- coding: utf-8 -*-
"""
affiliate_links.py — turn a raw product URL into the right affiliate link.

Amazon links already carry our tag (?tag=thegothicvaul-20) in the catalog, so
those pass through untouched. AliExpress links are wrapped through our Admitad
deeplink (joined 2026-08-12, ad space "Stiletto Vault Website" 2984135):

    https://rzekl.com/g/1e8d1144949a9d9ab95916525dc3e8/?ulp=<url-encoded target>

The wrapper token is per-account/program/ad-space; override via env
ALIEXPRESS_DEEPLINK_BASE if it ever changes.
"""
import os, urllib.parse

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

ALIEXPRESS_DEEPLINK_BASE = os.getenv(
    "ALIEXPRESS_DEEPLINK_BASE",
    "https://rzekl.com/g/1e8d1144949a9d9ab95916525dc3e8/",
).rstrip("/") + "/"

AMAZON_TAG = os.getenv("AMAZON_TAG", "thegothicvaul-20")


def aliexpress(url, subid=""):
    """Wrap an AliExpress product/category URL in our Admitad deeplink."""
    q = "?ulp=" + urllib.parse.quote(url, safe="")
    if subid:
        q = f"?subid={urllib.parse.quote(subid)}&ulp=" + urllib.parse.quote(url, safe="")
    return ALIEXPRESS_DEEPLINK_BASE + q


def amazon(url):
    """Ensure an Amazon URL carries our associate tag."""
    parts = urllib.parse.urlparse(url)
    qs = dict(urllib.parse.parse_qsl(parts.query))
    qs["tag"] = AMAZON_TAG
    return urllib.parse.urlunparse(parts._replace(query=urllib.parse.urlencode(qs)))


def affiliate_link(item, subid=""):
    """Best affiliate link for a catalog item, chosen by domain.
    Falls back to any pre-set aff_link, then the raw url."""
    url = item.get("url", "") or item.get("aff_link", "")
    domain = (item.get("domain", "") or url).lower()
    if "aliexpress." in domain:
        return aliexpress(url, subid)
    if "amazon." in domain:
        return item.get("aff_link") or amazon(url)
    return item.get("aff_link") or url


if __name__ == "__main__":
    demo = {"url": "https://www.aliexpress.com/item/1005001749588706.html",
            "domain": "aliexpress.com"}
    print("AliExpress →", affiliate_link(demo))
    print("Amazon     →", affiliate_link(
        {"url": "https://www.amazon.com/dp/B0F7LSL3G1", "domain": "amazon.com"}))
