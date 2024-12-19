class SplitMessageError(Exception):
    pass

class NotEnoughFragmentLen(SplitMessageError):
    def __init__(self, fragment, tag_str, remaining, max_len):
        super().__init__(f"Cannot add '{tag_str}' to fragment '{fragment}' with max length {max_len}.")
        self.fragment = fragment
        self.tag_str = tag_str
        self.remaining = remaining
        self.max_len = max_len

class NotEnoughFragmentLenForInitialization(SplitMessageError):
    def __init__(self, max_len):
        super().__init__(f"Not enough fragment length ({max_len}) for even starting a fragment.")
        self.max_len = max_len

class EmptySourceString(SplitMessageError):
    def __init__(self):
        super().__init__("The source string is empty.")
