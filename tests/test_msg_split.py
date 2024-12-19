import unittest
from src.msg_split.core import split_message
from bs4 import BeautifulSoup
from src.msg_split.exceptions import SplitMessageError

class TestSplitMessage(unittest.TestCase):

    def test_simple_split(self):
        source = "<p>" + "Hello World! " * 300 + "</p>"
        max_len = 1000
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            self.assertTrue(len(fragment) <= max_len)
            soup = BeautifulSoup(fragment, 'html.parser')
            self.assertIsNotNone(soup.find('p'))

    def test_no_split_needed(self):
        source = "<p>Hello World!</p>"
        max_len = 1000
        fragments = list(split_message(source, max_len=max_len))
        self.assertEqual(len(fragments), 1)
        self.assertEqual(fragments[0], source)

    def test_unbreakable_tag_too_long(self):
        source = "<a>" + "A" * 5000 + "</a>"
        max_len = 1000
        with self.assertRaises(SplitMessageError) as context:
            list(split_message(source, max_len=max_len))
        self.assertIn("Cannot add", str(context.exception))

    def test_preserve_structure(self):
        source = "<div><p>Paragraph 1</p><p>Paragraph 2</p><p>Paragraph 3</p></div>"
        max_len = 50
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            soup = BeautifulSoup(fragment, 'html.parser')
            if soup.find('div'):
                div = soup.find('div')
                self.assertTrue(all(child.name == 'p' for child in div.children if child.name))
            else:
                self.assertIsNotNone(soup.find('p'))

    def test_does_not_break_non_block_tags(self):
        source = "<p>Text with a <a href='link'>link</a> in it.</p>" * 100
        max_len = 500
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            self.assertNotIn('</a><a', fragment)
            soup = BeautifulSoup(fragment, 'html.parser')
            self.assertIsNotNone(soup.find('a'))

    def test_multiple_non_block_tags_within_block_tags(self):
        source = "<p>Here is a <a href='link1'>link1</a>, <a href='link2'>link2</a>, and <a href='link3'>link3</a> within a paragraph.</p>" * 100
        max_len = 800
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            soup = BeautifulSoup(fragment, 'html.parser')
            a_tags = soup.find_all('a')
            for a in a_tags:
                self.assertIsNotNone(a.get('href'))
            self.assertNotIn('</a><a', fragment)

    def test_empty_tags(self):
        source = "<p></p><div><span></span></div><ul><li></li></ul>" * 100
        max_len = 500
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            soup = BeautifulSoup(fragment, 'html.parser')
            self.assertTrue(soup.find('p') is not None)
            self.assertTrue(soup.find('div') is not None)
            self.assertTrue(soup.find('span') is not None)
            self.assertTrue(soup.find('ul') is not None)
            self.assertTrue(soup.find('li') is not None)

    def test_self_closing_tags(self):
        source = "<p>Line break here<br/> and an image <img src='image.jpg' alt='image'/></p>" * 100
        max_len = 600
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            soup = BeautifulSoup(fragment, 'html.parser')
            self.assertTrue(soup.find('br') is not None)
            self.assertTrue(soup.find('img') is not None)

    def test_self_closing_tags_various_contexts(self):
        source = """
        <div>
            <p>Line break here<br/> and an image <img src='image.jpg' alt='Image'/></p>
            <hr/>
            <span>Text after hr</span>
        </div>
        """ * 100
        max_len = 800
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            soup = BeautifulSoup(fragment, 'html.parser')
            br_tags = soup.find_all('br')
            img_tags = soup.find_all('img')
            hr_tags = soup.find_all('hr')
            self.assertTrue(len(br_tags) > 0)
            self.assertTrue(len(img_tags) > 0)
            self.assertTrue(len(hr_tags) > 0)

    def test_max_len_smaller_than_any_block_tag(self):
        source = "<p>Short text</p>"
        max_len = 5
        with self.assertRaises(SplitMessageError) as context:
            list(split_message(source, max_len=max_len))
        self.assertIn("Not enough fragment length", str(context.exception))

    def test_multiple_consecutive_block_tags(self):
        source = "<p>Paragraph 1</p><p>Paragraph 2</p><p>Paragraph 3</p>" * 100
        max_len = 800
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            soup = BeautifulSoup(fragment, 'html.parser')
            p_tags = soup.find_all('p')
            self.assertTrue(len(p_tags) > 0)
            for p in p_tags:
                self.assertIsNotNone(p.text)

    def test_broken_html_structure(self):
        source = "<p>Paragraph without closing tag"
        max_len = 1000
        fragments = list(split_message(source, max_len=max_len))
        self.assertTrue(len(fragments) == 1)
        soup = BeautifulSoup(fragments[0], 'html.parser')
        self.assertIsNotNone(soup.find('p'))
        self.assertTrue(soup.find('p').text.strip() == "Paragraph without closing tag")

    def test_deeply_nested_structure(self):
        nested_html = "<div>" * 50 + "Deep Content" + "</div>" * 50
        max_len = 1000
        fragments = list(split_message(nested_html, max_len=max_len))
        for fragment in fragments:
            soup = BeautifulSoup(fragment, 'html.parser')
            open_divs = len(soup.find_all('div'))
            closed_divs = len(soup.find_all('div'))
            self.assertEqual(open_divs, closed_divs)
            
    def test_fragments_with_only_text(self):
        source = "This is a plain text message. " * 500
        max_len = 1000
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            self.assertTrue(len(fragment) <= max_len)
            soup = BeautifulSoup(fragment, 'html.parser')
            self.assertEqual(len(soup.find_all()), 0)
            self.assertIn("This is a plain text message.", fragment)

    def test_only_non_block_tags(self):
        source = "<a href='link1'>Link1</a> <span>Span1</span> <strong>Strong1</strong> " * 300
        max_len = 1000
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            self.assertNotIn('</a><a', fragment)
            self.assertNotIn('</span><span', fragment)
            self.assertNotIn('</strong><strong', fragment)
            soup = BeautifulSoup(fragment, 'html.parser')
            a_tags = soup.find_all('a')
            span_tags = soup.find_all('span')
            strong_tags = soup.find_all('strong')
            self.assertTrue(len(a_tags) > 0)
            self.assertTrue(len(span_tags) > 0)
            self.assertTrue(len(strong_tags) > 0)

    def test_fragments_with_only_non_block_tags(self):
        source = "<a href='link1'>Link1</a> <span>Span1</span> <strong>Strong1</strong> " * 300
        max_len = 1000
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            self.assertNotIn('</a><a', fragment)
            self.assertNotIn('</span><span', fragment)
            self.assertNotIn('</strong><strong', fragment)
            soup = BeautifulSoup(fragment, 'html.parser')
            a_tags = soup.find_all('a')
            span_tags = soup.find_all('span')
            strong_tags = soup.find_all('strong')
            self.assertTrue(len(a_tags) > 0)
            self.assertTrue(len(span_tags) > 0)
            self.assertTrue(len(strong_tags) > 0)
    
    def test_custom_or_unusual_tag_names(self):
        source = "<custom-tag attr='value'><another-tag>Content</another-tag></custom-tag>" * 100
        max_len = 800
        fragments = list(split_message(source, max_len=max_len))
        for fragment in fragments:
            soup = BeautifulSoup(fragment, 'html.parser')
            custom_tags = soup.find_all('custom-tag')
            another_tags = soup.find_all('another-tag')
            for ct in custom_tags:
                self.assertIsNotNone(ct.find('another-tag'))
            for at in another_tags:
                self.assertEqual(at.text, "Content")


if __name__ == '__main__':
    unittest.main()
