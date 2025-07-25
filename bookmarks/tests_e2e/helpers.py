from django.contrib.staticfiles.testing import LiveServerTestCase
from playwright.sync_api import BrowserContext, Playwright, Page
from playwright.sync_api import expect

from bookmarks.tests.helpers import BookmarkFactoryMixin


class LinkdingE2ETestCase(LiveServerTestCase, BookmarkFactoryMixin):
    def setUp(self) -> None:
        self.client.force_login(self.get_or_create_test_user())
        self.cookie = self.client.cookies["sessionid"]

    def setup_browser(self, playwright) -> BrowserContext:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(
            [
                {
                    "name": "sessionid",
                    "value": self.cookie.value,
                    "domain": self.live_server_url.replace("http:", ""),
                    "path": "/",
                }
            ]
        )
        return context

    def open(self, url: str, playwright: Playwright) -> Page:
        browser = self.setup_browser(playwright)
        self.page = browser.new_page()
        self.page.goto(self.live_server_url + url)
        self.page.on("load", self.on_load)
        self.num_loads = 0
        return self.page

    def on_load(self):
        self.num_loads += 1

    def assertReloads(self, count: int):
        self.assertEqual(self.num_loads, count)

    def resetReloads(self):
        self.num_loads = 0

    def locate_bookmark_list(self):
        return self.page.locator("ul[ld-bookmark-list]")

    def locate_bookmark(self, title: str):
        bookmark_tags = self.page.locator("li[ld-bookmark-item]")
        return bookmark_tags.filter(has_text=title)

    def count_bookmarks(self):
        bookmark_tags = self.page.locator("li[ld-bookmark-item]")
        return bookmark_tags.count()

    def locate_details_modal(self):
        return self.page.locator(".modal.bookmark-details")

    def open_details_modal(self, bookmark):
        details_button = self.locate_bookmark(bookmark.title).get_by_text("View")
        details_button.click()

        details_modal = self.locate_details_modal()
        expect(details_modal).to_be_visible()

        return details_modal

    def locate_bulk_edit_bar(self):
        return self.page.locator(".bulk-edit-bar")

    def locate_bulk_edit_select_all(self):
        return self.locate_bulk_edit_bar().locator("label.bulk-edit-checkbox.all")

    def locate_bulk_edit_select_across(self):
        return self.locate_bulk_edit_bar().locator("label.select-across")

    def locate_bulk_edit_toggle(self):
        return self.page.get_by_title("Bulk edit")

    def select_bulk_action(self, value: str):
        return (
            self.locate_bulk_edit_bar()
            .locator('select[name="bulk_action"]')
            .select_option(value)
        )

    def navigate_menu(self, main_menu_item: str, sub_menu_item: str | None = None):
        if sub_menu_item:
            self.page.locator("nav").get_by_role("button", name=main_menu_item).click()
            self.page.locator("nav ul.menu").get_by_text(
                sub_menu_item, exact=True
            ).click()
        else:
            self.page.locator("nav").get_by_text(main_menu_item, exact=True).click()
