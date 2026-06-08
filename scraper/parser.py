from bs4 import BeautifulSoup


def parse_products(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    products = []

    cards = soup.select(".product")

    print(f"Found {len(cards)} product cards")

    for card in cards:

        try:

            name_tag = card.find("a")

            name = (
                name_tag.get_text(strip=True)
                if name_tag else "No Name"
            )

            link = ""

            if (
                name_tag and
                name_tag.get("href")
            ):

                href = name_tag["href"]

                if href.startswith("/"):

                    link = (
                        "https://shop.kingarthurbaking.com"
                        + href
                    )

                else:

                    link = href

            price_tag = card.select_one(
                ".price"
            )

            price = (
                price_tag.get_text(strip=True)
                if price_tag else "No Price"
            )

            products.append(
                {
                    "name": name,
                    "price": price,
                    "link": link,
                }
            )

        except Exception as e:

            print(e)

    return products