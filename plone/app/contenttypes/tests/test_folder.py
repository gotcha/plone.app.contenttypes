from plone.app.contenttypes.browser.folder import FolderView
from plone.app.contenttypes.interfaces import IFolder
from plone.app.contenttypes.testing import (  # noqa
    PLONE_APP_CONTENTTYPES_FUNCTIONAL_TESTING,
)
from plone.app.contenttypes.testing import (  # noqa
    PLONE_APP_CONTENTTYPES_INTEGRATION_TESTING,
)
from plone.app.contenttypes.tests.test_image import dummy_image
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from plone.testing.zope import Browser
from zope.component import createObject
from zope.component import queryUtility

import unittest


class FolderIntegrationTest(unittest.TestCase):
    layer = PLONE_APP_CONTENTTYPES_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.request["ACTUAL_URL"] = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])

    def test_schema(self):
        fti = queryUtility(IDexterityFTI, name="Folder")
        schema = fti.lookupSchema()
        self.assertTrue(schema.getName().endswith("_0_Folder"))

    def test_fti(self):
        fti = queryUtility(IDexterityFTI, name="Folder")
        self.assertNotEqual(None, fti)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI, name="Folder")
        factory = fti.factory
        new_object = createObject(factory)
        self.assertTrue(IFolder.providedBy(new_object))

    def test_adding(self):
        self.portal.invokeFactory("Folder", "doc1")
        self.assertTrue(IFolder.providedBy(self.portal["doc1"]))


class FolderViewIntegrationTest(unittest.TestCase):
    layer = PLONE_APP_CONTENTTYPES_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.request["ACTUAL_URL"] = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])

    def test_result_filtering(self):
        """Test, if portal_state's friendly_types and the result method's
        keyword arguments are included in the query.
        """

        self.portal.invokeFactory("News Item", "newsitem")
        self.portal.invokeFactory("Document", "document")
        view = FolderView(self.portal, self.request)

        # Test, if all results are found.
        view.portal_state.friendly_types = lambda: ["Document", "News Item"]
        res = view.results()
        self.assertEqual(len(res), 2)

        # Test, if friendly_types does filter for types.
        view.portal_state.friendly_types = lambda: ["Document"]
        res = view.results()
        self.assertEqual(len(res), 1)

        # Test, if friendly_types does filter for types.
        view.portal_state.friendly_types = lambda: ["NotExistingType"]
        res = view.results()
        self.assertEqual(len(res), 0)

        # Test, if kwargs filtering is applied.
        view.portal_state.friendly_types = lambda: ["NotExistingType"]
        res = view.results(
            object_provides="plone.app.contenttypes.interfaces.IDocument"
        )
        self.assertEqual(len(res), 1)

    def test_result_batching(self):
        for idx in range(5):
            self.portal.invokeFactory("Document", f"document{idx}")
        request = self.request.clone()
        request.form["b_size"] = 5
        view = FolderView(self.portal, request)

        batch = view.batch()
        self.assertEqual(batch.length, 5)
        self.assertEqual(len([item for item in batch]), 5)
        self.assertFalse(batch.has_next)

        self.portal.invokeFactory("Document", "document5")

        batch = view.batch()
        self.assertEqual(batch.length, 6)
        self.assertEqual(len([item for item in batch]), 6)
        self.assertFalse(batch.has_next)

        self.portal.invokeFactory("Document", "document6")

        batch = view.batch()
        self.assertEqual(batch.length, 5)
        self.assertEqual(len([item for item in batch]), 5)
        self.assertTrue(batch.has_next)
        self.assertEqual(batch.next_item_count, 2)


class FolderFunctionalTest(unittest.TestCase):
    layer = PLONE_APP_CONTENTTYPES_FUNCTIONAL_TESTING

    def setUp(self):
        app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            "Authorization",
            "Basic {}:{}".format(
                SITE_OWNER_NAME,
                SITE_OWNER_PASSWORD,
            ),
        )

    def test_add_folder(self):
        self.browser.open(self.portal_url)
        self.browser.getLink(url="http://nohost/plone/++add++Folder").click()
        widget = "form.widgets.IDublinCore.title"
        self.browser.getControl(name=widget).value = "My folder"
        widget = "form.widgets.IShortName.id"
        self.browser.getControl(name=widget).value = ""
        widget = "form.widgets.IDublinCore.description"
        self.browser.getControl(name=widget).value = "This is my folder."
        self.browser.getControl("Save").click()
        self.assertTrue(self.browser.url.endswith("my-folder/view"))
        self.assertTrue("My folder" in self.browser.contents)
        self.assertTrue("This is my folder" in self.browser.contents)

    def test_add_folder_with_shortname(self):
        self.browser.open(self.portal_url)
        self.browser.getLink(url="http://nohost/plone/++add++Folder").click()
        widget = "form.widgets.IDublinCore.title"
        self.browser.getControl(name=widget).value = "My folder"
        widget = "form.widgets.IShortName.id"
        self.browser.getControl(name=widget).value = "my-special-folder"
        self.browser.getControl("Save").click()
        self.assertTrue(self.browser.url.endswith("my-special-folder/view"))


class FolderViewFunctionalTest(unittest.TestCase):
    layer = PLONE_APP_CONTENTTYPES_FUNCTIONAL_TESTING

    def setUp(self):
        app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal_url = self.portal.absolute_url()
        self.portal.invokeFactory("Folder", id="folder", title="My Folder")
        self.folder = self.portal.folder
        self.folder_url = self.folder.absolute_url()
        self.folder.invokeFactory("Document", id="doc1", title="Document 1")
        import transaction

        transaction.commit()
        self.browser = Browser(app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            "Authorization",
            "Basic {}:{}".format(
                SITE_OWNER_NAME,
                SITE_OWNER_PASSWORD,
            ),
        )

    def test_folder_view(self):
        self.browser.open(self.folder_url + "/view")
        self.assertIn("My Folder", self.browser.contents)
        self.assertIn("Document 1", self.browser.contents)

    def test_folder_summary_view(self):
        self.browser.open(self.folder_url + "/summary_view")
        self.assertIn("My Folder", self.browser.contents)
        self.assertIn("Document 1", self.browser.contents)

    def test_folder_full_view(self):
        self.browser.open(self.folder_url + "/full_view")
        self.assertIn("My Folder", self.browser.contents)
        self.assertIn("Document 1", self.browser.contents)

    def test_folder_tabular_view(self):
        self.browser.open(self.folder_url + "/tabular_view")
        self.assertIn("My Folder", self.browser.contents)
        self.assertIn("Document 1", self.browser.contents)

    def test_folder_album_view(self):
        self.folder.invokeFactory("Image", id="image1", title="Image 1")
        img1 = self.folder["image1"]
        img1.image = dummy_image()
        import transaction

        transaction.commit()
        self.browser.open(self.folder_url + "/album_view")
        self.assertIn("My Folder", self.browser.contents)
        self.assertIn(
            '<img src="http://nohost/plone/folder/image1/@@images',
            self.browser.contents,
        )

    def test_list_item_wout_title(self):
        """In content listings, if a content object has no title use it's id."""
        self.folder.invokeFactory("Document", id="doc_wout_title")
        import transaction

        transaction.commit()

        # Document should be shown in listing view (and it's siblings)
        self.browser.open(self.folder_url + "/listing_view")
        self.assertIn("doc_wout_title", self.browser.contents)

        # And also in tabular view
        self.browser.open(self.folder_url + "/tabular_view")
        self.assertIn("doc_wout_title", self.browser.contents)
