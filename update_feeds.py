import feedparser
import json
import html
import re
import requests
from datetime import datetime, timezone


FEEDS = {

    "Bloody Disgusting":
        "https://bloody-disgusting.com/feed",

    "Den of Geek":
        "https://www.denofgeek.com/feed/",

    "Fangoria":
        "https://www.fangoria.com/feed/",

    "PlayStation Lifestyle":
        "https://www.playstationlifestyle.net/feed/",

    "PlayStation Blog":
        "https://blog.playstation.com/feed/",

    "Push Square":
        "https://www.pushsquare.com/feeds/latest",

    "Steam":
        "https://store.steampowered.com/feeds/news.xml",

    "Steam Game Deals":
        "https://www.steamgamesales.com/rss"

}


def clean_text(value):

    if not value:
        return ""

    value = html.unescape(value)

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def find_image(entry):

    # Media RSS
    media_content = entry.get(
        "media_content",
        []
    )

    if media_content:

        for media in media_content:

            url = media.get("url")

            if url:
                return url


    # Media thumbnail
    media_thumbnail = entry.get(
        "media_thumbnail",
        []
    )

    if media_thumbnail:

        for media in media_thumbnail:

            url = media.get("url")

            if url:
                return url


    # Enclosure
    enclosures = entry.get(
        "enclosures",
        []
    )

    for enclosure in enclosures:

        url = (
            enclosure.get("href")
            or
            enclosure.get("url")
        )

        if url:

            media_type = enclosure.get(
                "type",
                ""
            )

            if (
                media_type.startswith("image")
                or not media_type
            ):

                return url


    # Image embedded in content
    content = entry.get(
        "content",
        []
    )

    for item in content:

        value = item.get(
            "value",
            ""
        )

        match = re.search(
            r'<img[^>]+src=["\']([^"\']+)',
            value,
            re.IGNORECASE
        )

        if match:

            return match.group(1)


    # Image embedded in description
    description = entry.get(
        "description",
        ""
    )

    match = re.search(
        r'<img[^>]+src=["\']([^"\']+)',
        description,
        re.IGNORECASE
    )

    if match:

        return match.group(1)


    return ""


def get_date(entry):

    parsed = entry.get(
        "published_parsed"
    )

    if not parsed:

        parsed = entry.get(
            "updated_parsed"
        )

    if parsed:

        try:

            return datetime(
                *parsed[:6],
                tzinfo=timezone.utc
            ).isoformat()

        except Exception:

            pass


    return entry.get(
        "published",
        ""
    )


def get_description(entry):

    description = entry.get(
        "summary",
        ""
    )

    if not description:

        description = entry.get(
            "description",
            ""
        )

    if not description:

        content = entry.get(
            "content",
            []
        )

        if content:

            description = content[0].get(
                "value",
                ""
            )


    return clean_text(
        description
    )


def main():

    output = {

        "updated":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "feeds": {}

    }


    for name, url in FEEDS.items():

        print(
            f"Fetching {name}: {url}"
        )


        try:

            response = requests.get(

                url,

                timeout=30,

                headers={

                    "User-Agent":
                    "Mozilla/5.0 RSS Reader"

                }

            )


            response.raise_for_status()


            feed = feedparser.parse(
                response.content
            )


            articles = []


            for entry in feed.entries[:10]:

                title = clean_text(
                    entry.get(
                        "title",
                        ""
                    )
                )


                link = entry.get(
                    "link",
                    ""
                )


                description =
                    get_description(
                        entry
                    )


                image =
                    find_image(
                        entry
                    )


                date =
                    get_date(
                        entry
                    )


                if not title:

                    continue


                articles.append({

                    "title":
                        title,

                    "link":
                        link,

                    "description":
                        description[:300],

                    "date":
                        date,

                    "image":
                        image

                })


            output["feeds"][name] = {

                "url":
                    url,

                "articles":
                    articles

            }


            print(
                f"  Found {len(articles)} articles"
            )


        except Exception as error:

            print(
                f"  ERROR: {error}"
            )


            output["feeds"][name] = {

                "url":
                    url,

                "articles":
                    [],

                "error":
                    str(error)

            }


    with open(
        "feeds.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(

            output,

            file,

            indent=2,

            ensure_ascii=False

        )


if __name__ == "__main__":

    main()
