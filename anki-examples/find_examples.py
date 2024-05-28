import os
import re
import numpy as np
import multiprocessing as mp

from multiprocessing import Manager


class CorpusExamples:

    def __init__(
        self,
        corpus_folder,
        min_words=4,
        max_words=15,
        num_processes=6,
        use_semantic_sorting=True,
    ):
        self.corpus = self.prepare_corpus(corpus_folder)
        print("Total Examples", sum([len(c[1]) for c in self.corpus]))
        self.min_words = min_words
        self.max_words = max_words
        self.num_processes = num_processes
        self.split_size = len(self.corpus) // num_processes

        self.manager = Manager()
        self.result_queue = self.manager.Queue()

        if use_semantic_sorting:
            print("Using semantic sorting.")
            from semantic_ranking import SimilarityRanker

            self.sort = lambda vi, results: SimilarityRanker().sort(
                vi, results, key=lambda x: x["text"]
            )
        else:
            self.sort = lambda _, results: sorted(
                results, key=lambda x: x["num_words"], reverse=True
            )

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

    def find_examples(self, example):

        ex_pattern = re.compile(re.escape(example), re.IGNORECASE)

        def process_search(corpus_split):
            """Find examples in the corpus that match the pattern. The examples should be put into the result_queue, as this is called from a sub-process."""
            found_examples = []
            for file_name, file_content in corpus_split:
                for line in file_content:
                    # Check case insensitive, and sentence should not go over word limit
                    contains_word = ex_pattern.search(line)
                    # Find start and end of match
                    line_split = line.split()
                    under_word_limit = len(line_split) < self.max_words
                    over_min_words = len(line_split) > self.min_words
                    if contains_word and under_word_limit and over_min_words:
                        start, end = ex_pattern.search(line).span()
                        found_examples.append(
                            {
                                "file": file_name,
                                "text": line,
                                "num_words": len(line_split),
                                "start": start,
                                "end": end,
                            }
                        )

            self.result_queue.put(found_examples)

        # Create and start the processes
        processes = []

        for i in range(self.num_processes):
            split_corpus = self.corpus[i * self.split_size : (i + 1) * self.split_size]

            p = mp.Process(target=process_search, args=(split_corpus,))
            p.start()
            processes.append(p)

        # Wait for all processes to finish
        for p in processes:
            p.join()

        # Collect the results from the Queue and concatenate them into a single list
        final_result = []
        while not self.result_queue.empty():
            final_result.extend(self.result_queue.get())

        final_result = self.sort(example, final_result)
        return final_result


if __name__ == "__main__":
    corpus_folder = "/media/ducha/SSDSHARED/VN/subs_dump/viet_subs_processed2"
    corpus_examples = CorpusExamples(corpus_folder)

    example = "cô gái"

    found_examples = corpus_examples.find_examples(example)

    print(found_examples)
    print("Done")
