import os
import re
import numpy as np
import cudf

os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"


class CorpusExamples:
    def __init__(
        self,
        corpus_folder,
        min_words=4,
        max_words=15,
        num_processes=6,
    ):
        self.corpus = self.prepare_corpus(corpus_folder)
        print("Total Examples", sum([len(c[1]) for c in self.corpus]))
        self.corpus_df: cudf.DataFrame = cudf.DataFrame(
            self.corpus, columns=["file", "text"]
        ).explode("text")

        self.corpus_df["num_words"] = self.corpus_df["text"].str.count(" ") + 1
        self.corpus_df = self.corpus_df[
            (self.corpus_df["num_words"] >= min_words)
            & (self.corpus_df["num_words"] <= max_words)
        ]
        print("Filtered Examples", len(self.corpus_df))

        self.num_processes = num_processes
        self.split_size = len(self.corpus) // num_processes

    def prepare_corpus(self, corpus_folder):
        """Prepare the corpus from the given folder.

        Each file in the folder is a document in the corpus, with an example sentence for each line.
        The corpus is a list of tuples with (file_name, file_content)."""

        print("Preparing corpus from", corpus_folder)

        def get_file(file_name):
            with open(os.path.join(corpus_folder, file_name), "r") as f:
                # Read each line and strip the newline character
                return set([line.strip() for line in f.readlines()])

        available_files = [fname for fname in os.listdir(corpus_folder)]

        # Assumes openSubs format
        corpus = [
            (file_name.rsplit(".", 4)[0], get_file(file_name))
            for file_name in available_files
        ]

        print("Corpus prepared with", len(corpus), "files")
        return np.array(corpus)

    def find_examples(self, example: str, num_examples: int):
        if not example or not num_examples:
            return []

        ex_escaped = re.escape(example)

        # cudf doesn't support case insensitive search, so we try lower case, upper case and title case
        ex_pattern = rf"(^|\W)({ex_escaped.lower()}|{ex_escaped.title()}|{ex_escaped.upper()})($|\W)"

        found_examples: cudf.DataFrame = self.corpus_df[
            self.corpus_df["text"].str.contains(ex_pattern)
        ]

        if len(found_examples) == 0:
            return []
        elif len(found_examples) <= num_examples:
            return found_examples.to_dict(orient="records")
        else:
            return found_examples.sample(n=num_examples).to_dict(orient="records")


if __name__ == "__main__":
    corpus_folder = "/mnt/SSDSHARED/VN/subs_dump/viet_subs_processed2"
    corpus_examples = CorpusExamples(corpus_folder)

    example = "từ"

    # Benchmark
    import time

    start = time.time()
    found_examples = corpus_examples.find_examples(example, num_examples=60000)
    end = time.time()
    print(len(found_examples), "examples found for", example)
    print(example, ":", [e["text"] for e in found_examples[:10]])
    print("Done")
    print("Time taken:", end - start)
