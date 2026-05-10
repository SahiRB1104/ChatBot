from markdown import markdown

try:
    import bleach
except ImportError:
    bleach = None

# Allowed tags and attributes for sanitized HTML output
ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "pre",
    "code",
    "br",
    "hr",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "a",
    "blockquote",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "code": ["class"],
}


def format_response_as_html(text: str) -> str:
    """Convert markdown/plain text to sanitized HTML.

    - Convert Markdown to HTML using `markdown`.
    - Sanitize resulting HTML with `bleach`.
    """
    if not text:
        return ""

    # Convert markdown to HTML first
    html = markdown(text, extensions=["extra", "sane_lists"]) if "<" not in text else text

    if bleach is None:
        return html

    # Sanitize HTML
    clean = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )

    return clean
