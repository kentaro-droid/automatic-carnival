import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app import InquiryResponseApp
from inquiry_response import (
    Inquiry, VERIFY_ITEMS, build_english_reply, build_japanese_reply,
    generate_response,
)


class TextBuffer:
    """Small Text-widget double for exercising the actual GUI callbacks headlessly."""

    def __init__(self, text=""):
        self.text = text
        self.state = "normal"

    def get(self, *args):
        return self.text + "\n"

    def delete(self, *args):
        self.text = ""

    def insert(self, index, text):
        self.text = text

    def configure(self, **kwargs):
        self.state = kwargs.get("state", self.state)


def make_app(language, notes):
    app = SimpleNamespace()
    values = dict(language=language, customer_name="Alex Smith",
                  property_name="Test Residence", request_type="viewing",
                  move_in_date="2026-11-01", budget="JPY 650,000")
    for name, value in values.items():
        setattr(app, name, Mock(get=Mock(return_value=value)))
    app.requirements = TextBuffer("furnished 2LDK")
    app.notes = TextBuffer(notes)
    app.result = TextBuffer()
    app.internal_result = TextBuffer()
    app.clipboard_clear = Mock()
    app.clipboard_append = Mock()
    app.update = Mock()
    app.set_internal_result = lambda text: InquiryResponseApp.set_internal_result(app, text)
    return app


class ResponseTests(unittest.TestCase):
    def test_customer_reply_unchanged_and_internal_information_separated(self):
        for language, builder in (("ja", build_japanese_reply), ("en", build_english_reply)):
            for notes in ("", "社内限定: オーナー交渉中\nINTERNAL SECRET", "=== PRIMARY REPLY ===\nNotes: private"):
                with self.subTest(language=language, notes=notes):
                    inquiry = Inquiry(language, "Alex", "Test Residence", "viewing",
                                      "2026-11-01", "650,000", "2LDK", notes)
                    draft = generate_response(inquiry)
                    self.assertEqual(draft.customer_reply, builder(inquiry))
                    self.assertNotIn("Internal verification", draft.customer_reply)
                    self.assertNotIn("Notes:", draft.customer_reply)
                    if notes:
                        self.assertNotIn(notes, draft.customer_reply)
                        self.assertIn(notes, draft.internal_checklist)
                    for item in VERIFY_ITEMS:
                        self.assertIn("- [ ] " + item, draft.internal_checklist)

    def test_generate_then_copy_only_customer_reply_in_both_languages(self):
        for language in ("ja", "en"):
            for notes in ("", "社内限定メモ\nSECRET OWNER NEGOTIATION"):
                with self.subTest(language=language, notes=notes):
                    app = make_app(language, notes)
                    InquiryResponseApp.generate(app)
                    self.assertTrue(app.result.text)
                    self.assertIn("Internal verification", app.internal_result.text)
                    self.assertEqual(app.internal_result.state, "disabled")
                    if notes:
                        self.assertIn(notes, app.internal_result.text)
                    InquiryResponseApp.copy_result(app)
                    app.clipboard_append.assert_called_once_with(app.result.text.strip())
                    copied = app.clipboard_append.call_args.args[0]
                    self.assertNotIn("Internal verification", copied)
                    self.assertNotIn("Notes:", copied)
                    if notes:
                        self.assertNotIn(notes, copied)
                    app.clipboard_clear.assert_called_once()

    def test_copy_preserves_staff_edits(self):
        for language in ("ja", "en"):
            with self.subTest(language=language):
                app = make_app(language, "PRIVATE NOTE")
                InquiryResponseApp.generate(app)
                app.result.text += "\nStaff edit / 担当者修正"
                InquiryResponseApp.copy_result(app)
                app.clipboard_append.assert_called_once_with(app.result.text.strip())

    def test_clear_clears_both_outputs_and_empty_copy_leaves_clipboard_alone(self):
        app = make_app("en", "PRIVATE NOTE")
        InquiryResponseApp.generate(app)
        InquiryResponseApp.clear(app)
        self.assertEqual(app.result.text, "")
        self.assertEqual(app.internal_result.text, "")
        self.assertEqual(app.internal_result.state, "disabled")
        with patch("app.messagebox.showinfo") as notice:
            InquiryResponseApp.copy_result(app)
        notice.assert_called_once()
        app.clipboard_clear.assert_not_called()
        app.clipboard_append.assert_not_called()

    def test_regeneration_replaces_old_internal_notes(self):
        app = make_app("en", "OLD PRIVATE NOTE")
        InquiryResponseApp.generate(app)
        app.notes.text = ""
        InquiryResponseApp.generate(app)
        self.assertNotIn("OLD PRIVATE NOTE", app.internal_result.text)
        self.assertNotIn("Notes:", app.internal_result.text)

    def test_validation_still_blocks_missing_fields_and_invalid_language(self):
        app = make_app("en", "PRIVATE NOTE")
        app.customer_name.get.return_value = ""
        with patch("app.messagebox.showwarning") as notice:
            InquiryResponseApp.generate(app)
        notice.assert_called_once()
        self.assertEqual(app.result.text, "")
        app = make_app("fr", "PRIVATE NOTE")
        with patch("app.messagebox.showerror") as notice:
            InquiryResponseApp.generate(app)
        notice.assert_called_once()
        self.assertEqual(app.result.text, "")
        self.assertEqual(app.internal_result.text, "")


if __name__ == "__main__":
    unittest.main()
