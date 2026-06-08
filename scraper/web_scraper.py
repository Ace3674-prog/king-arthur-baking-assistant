from playwright.sync_api import (
    sync_playwright
)

from scraper.parser import (
    parse_products
)

from scraper.detail_parser import (
    parse_product_detail
)

BASE_URL = (
    "https://shop.kingarthurbaking.com/mixes"
)


def scrape_mixes():

    print("Starting scraper...")

    all_products = []

    visited_links = set()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        current_page = 1

        while True:

            url = (
                f"{BASE_URL}?page="
                f"{current_page}"
            )

            print(
                f"\nOpening page "
                f"{current_page}"
            )

            print(url)

            try:

                # =========================
                # OPEN CATEGORY PAGE
                # =========================

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=120000
                )

                page.wait_for_timeout(3000)

                html = page.content()

                products = parse_products(
                    html
                )

                print(
                    f"Found "
                    f"{len(products)} products"
                )

                # Stop if no products
                if not products:

                    print(
                        "No more products found"
                    )

                    break

                # =========================
                # DETAIL PAGE SCRAPING
                # =========================

                for product in products:

                    try:

                        # Skip duplicates
                        if (
                            product["link"]
                            in visited_links
                        ):

                            continue

                        visited_links.add(
                            product["link"]
                        )

                        print(
                            f"\nOpening detail:"
                        )

                        print(
                            product["link"]
                        )

                        # Open detail page
                        page.goto(
                            product["link"],
                            wait_until=(
                                "domcontentloaded"
                            ),
                            timeout=120000
                        )

                        page.wait_for_timeout(
                            2000
                        )

                        ingredients_tab = page.query_selector(
                            "#ingredients-tab"
                        )

                        if ingredients_tab:
                            ingredients_tab.click()
                            page.wait_for_timeout(
                                3000
                            )

                        detail_html = (
                            page.content()
                        )

                        details = (
                            parse_product_detail(
                                detail_html
                            )
                        )

                        # Merge detail data
                        product.update(
                            details
                        )

                        all_products.append(
                            product
                        )

                        print(
                            f"Saved:"
                            f" {product.get('name')}"
                        )

                    except Exception as e:

                        print(
                            f"Detail scrape failed:"
                            f" {e}"
                        )

                current_page += 1

            except Exception as e:

                print(
                    f"Page scrape failed:"
                    f" {e}"
                )

                break

        browser.close()

    print(
        f"\nCollected "
        f"{len(all_products)} products"
    )

    return all_products