from typing import Generator, Union
from bs4 import BeautifulSoup, NavigableString, Tag

MAX_LEN = 4096

from .exceptions import NotEnoughFragmentLen, NotEnoughFragmentLenForInitialization, EmptySourceString

def get_attr(k: str, v: Union[str, int]) -> str:
    return f'{k}="{v}"'

def get_open_tag(tag: Tag) -> str:
    attrs = ""
    if tag.attrs:
        attrs = " " + " ".join(get_attr(k, v) for k, v in tag.attrs.items())
    return f"<{tag.name}{attrs}>"

def get_close_tag(name: str) -> str:
    return f"</{name}>"

def get_open_tags(tags: list[Tag]) -> str:
    return "".join(get_open_tag(t) for t in tags)

def get_close_tags(tags: list[Tag]) -> str:
    return "".join(get_close_tag(t.name) for t in reversed(tags))

def tokenize(soup: BeautifulSoup):
    def recurse(node):
        if isinstance(node, NavigableString):
            text = str(node)
            if text.strip() == "" and text != "\n":
                pass
            yield ("text", text)
        elif isinstance(node, Tag):
            yield ("open", node)
            for child in node.contents:
                yield from recurse(child)
            yield ("close", node.name)

    for c in soup.contents:
        yield from recurse(c)

def split_message(source: str, max_len=MAX_LEN) -> Generator[str, None, None]:
    if not isinstance(max_len, int):
        raise TypeError("max_len must be an integer")

    if not source.strip():
        raise EmptySourceString()

    block_tags = {"p", "b", "strong", "i", "ul", "ol", "div", "span"}

    soup = BeautifulSoup(source, "html.parser")
    tokens = list(tokenize(soup))

    open_blocks: list[Tag] = []
    fragment = ""

    def current_len_with_closers(additional_len=0):
        return len(fragment) + additional_len + len(get_close_tags(open_blocks))

    def flush_fragment():
        return fragment + get_close_tags(open_blocks)

    def start_new_fragment(reopen=True):
        return get_open_tags(open_blocks) if reopen else ""

    def yield_fragment():
        nonlocal fragment
        res = flush_fragment()
        yield_frag = res
        fragment = ""
        return yield_frag

    i = 0
    n = len(tokens)
    while i < n:
        token = tokens[i]
        if token[0] == "open":
            tag = token[1]
            tag_str = get_open_tag(tag)

            if tag.name in block_tags:
                if current_len_with_closers(len(tag_str)) > max_len:
                    if fragment:
                        res = yield_fragment()
                        yield res
                        fragment = start_new_fragment(reopen=True)
                        if current_len_with_closers(len(tag_str)) > max_len:
                            raise NotEnoughFragmentLen(fragment, tag_str, "", max_len)
                    else:
                        raise NotEnoughFragmentLenForInitialization(max_len)
                fragment += tag_str
                open_blocks.append(tag)
                i += 1
            else:
                sub_fragment = tag_str
                depth = 1
                j = i + 1
                while j < n and depth > 0:
                    tk = tokens[j]
                    if tk[0] == "open":
                        sub_fragment += get_open_tag(tk[1])
                        depth += 1
                    elif tk[0] == "close":
                        sub_fragment += get_close_tag(tk[1])
                        depth -= 1
                    elif tk[0] == "text":
                        sub_fragment += tk[1]
                    j += 1

                if depth != 0:
                    raise ValueError("Unmatched tags in input")

                if current_len_with_closers(len(sub_fragment)) > max_len:
                    if fragment:
                        res = yield_fragment()
                        yield res
                        fragment = start_new_fragment(reopen=True)
                        if current_len_with_closers(len(sub_fragment)) > max_len:
                            raise NotEnoughFragmentLen(fragment, sub_fragment, "", max_len)
                    else:
                        raise NotEnoughFragmentLen(sub_fragment, sub_fragment, "", max_len)

                fragment += sub_fragment
                i = j
        elif token[0] == "close":
            tag_name = token[1]
            close_str = get_close_tag(tag_name)
            if tag_name in {t.name for t in open_blocks}:
                if current_len_with_closers(len(close_str)) > max_len:
                    if fragment:
                        res = yield_fragment()
                        yield res
                        fragment = start_new_fragment(reopen=True)
                        if current_len_with_closers(len(close_str)) > max_len:
                            raise NotEnoughFragmentLen(fragment, close_str, "", max_len)
                    else:
                        raise NotEnoughFragmentLenForInitialization(max_len)

                for idx in range(len(open_blocks)-1, -1, -1):
                    if open_blocks[idx].name == tag_name:
                        fragment += close_str
                        open_blocks.pop(idx)
                        break
                i += 1
            else:
                raise ValueError("Close tag without matching open tag encountered")
        elif token[0] == "text":
            txt = token[1]
            remaining = txt
            while remaining:
                if current_len_with_closers(len(remaining)) <= max_len:
                    fragment += remaining
                    remaining = ""
                else:
                    space_left = max_len - current_len_with_closers()
                    if space_left <= 0:
                        if fragment:
                            res = yield_fragment()
                            yield res
                            fragment = start_new_fragment(reopen=True)
                            space_left = max_len - current_len_with_closers()
                            if space_left <= 0:
                                raise NotEnoughFragmentLenForInitialization(max_len)
                        else:
                            raise NotEnoughFragmentLenForInitialization(max_len)
                    chunk = remaining[:space_left]
                    fragment += chunk
                    remaining = remaining[len(chunk):]
            i += 1
        else:
            raise ValueError("Unknown token type")

    if fragment or open_blocks:
        yield flush_fragment()
