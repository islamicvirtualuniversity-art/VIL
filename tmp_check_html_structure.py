from html.parser import HTMLParser

class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag in ['br','hr','img','input','meta','link','area','base','col','command','embed','keygen','param','source','track','wbr']:
            return
        self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if not self.stack:
            self.errors.append(('unmatched end', tag, self.getpos()))
            return
        last, pos = self.stack.pop()
        if last != tag:
            self.errors.append(('mismatch', last, tag, pos, self.getpos()))

checker = TagChecker()
text = open('course-islamic-studies.html', encoding='utf-8').read()
checker.feed(text)
print('errors:', checker.errors[:20])
print('stack tail:', checker.stack[-20:])
