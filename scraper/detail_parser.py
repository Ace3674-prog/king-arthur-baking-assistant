from bs4 import BeautifulSoup
import re


def parse_product_detail(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # =========================
    # PRODUCT NAME
    # =========================

    name_tag = soup.select_one(
        "h1"
    )

    name = (
        name_tag.get_text(strip=True)
        if name_tag else ""
    )

    # =========================
    # PRICE
    # =========================

    price_tag = soup.select_one(
        ".orig-price"
    )

    price = (
        price_tag.get_text(strip=True)
        if price_tag else ""
    )

    # =========================
    # DESCRIPTION
    # =========================

    desc_tag = soup.select_one(
        ".productView-description .tab-content-left"
    )

    if not desc_tag:
        desc_tag = soup.select_one(
            ".productView-description"
        )

    description = (
        desc_tag.get_text(
            separator=" ",
            strip=True
        )
        if desc_tag else ""
    )

    # =========================
    # SKU
    # =========================

    sku = ""

    sku_text = soup.get_text()

    sku_match = re.search(
        r"SKU[:\s]*(\d+)",
        sku_text
    )

    if sku_match:

        sku = sku_match.group(1)

    # =========================
    # RATING + REVIEWS
    # =========================

    rating = ""
    reviews = ""

    rating_widget = soup.select_one(
        ".kab-product-rating"
    )

    if rating_widget:

        rating = rating_widget.get(
            "data-rating",
            ""
        )

        reviews = rating_widget.get(
            "data-reviews",
            ""
        )

    # =========================
    # IMAGES
    # =========================

    images = []

    image_tags = soup.select(
        "img"
    )

    for img in image_tags:

        src = img.get("src")

        if (
            src and
            "products" in src
        ):

            images.append(src)

    # Remove duplicates
    images = list(set(images))

    # =========================
    # INGREDIENTS
    # =========================

    ingredients = ""

    ingredients_section = soup.select_one(
        "#ingredients-nutrition-and-allergens, .tab-content#ingredients-nutrition-and-allergens"
    )

    if ingredients_section:
        ingredients_html = ingredients_section.select_one(
            ".ingredients-html"
        )

        if ingredients_html:
            ingredients = ""

            ingredient_heading = None
            for heading in ingredients_html.select("h3"):
                if "ingredient" in heading.get_text(strip=True).lower():
                    ingredient_heading = heading
                    break

            if ingredient_heading:
                ingredient_paragraph = (
                    ingredient_heading.find_next_sibling("p")
                )
                if ingredient_paragraph:
                    ingredients = (
                        ingredient_paragraph.get_text(
                            separator=" ",
                            strip=True
                        )
                    )

            if not ingredients:
                first_paragraph = ingredients_html.select_one("p")
                if first_paragraph:
                    ingredients = (
                        first_paragraph.get_text(
                            separator=" ",
                            strip=True
                        )
                    )

            if not ingredients:
                ingredients = (
                    ingredients_html.get_text(
                        separator=" ",
                        strip=True
                    )
                )

        if ingredients:
            ingredients = re.sub(
                r"View Product Packaging \(\.pdf\)",
                "",
                ingredients,
                flags=re.IGNORECASE
            )
            ingredients = re.sub(
                r"\s+",
                " ",
                ingredients
            ).strip()

    return {
        "name": name,
        "price": price,
        "description": description,
        "rating": rating,
        "reviews": reviews,
        "sku": sku,
        "images": images,
        "ingredients": ingredients,
    }