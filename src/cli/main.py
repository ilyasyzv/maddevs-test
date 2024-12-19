import click
from ..msg_split.core import split_message

@click.command()
@click.option("--max-len", default=4096, type=int, help="Maximum length of each fragment")
@click.argument("input_file", type=click.Path(exists=True))
def process_file(max_len, input_file):
    with open(input_file, "r", encoding="utf-8") as source:
        fragments = split_message(source.read(), max_len=max_len)
        i = 1
        try:
            for res in fragments:
                print(f"fragment #{i}: {len(res)} chars.")
                print(res)
                i += 1
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    process_file()
