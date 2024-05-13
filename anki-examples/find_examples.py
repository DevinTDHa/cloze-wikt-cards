import os
import re
import numpy as np
import multiprocessing as mp

from multiprocessing import Manager


output_folder = "/media/ducha/SSDSHARED/VN/subs_dump/viet_subs_processed2"


def prepare_corpus(output_folder):
    """Prepare the corpus from the output folder. The corpus is a list of tuples with (file_name, file_content).
    """
    print("Preparing corpus from", output_folder)
    def get_file(file_name):
        with open(os.path.join(output_folder, file_name), "r") as f:
            # Read each line and strip the newline character
            return set([line.strip() for line in f.readlines()])

    # List all files in the folder, that are actually vietnamese
    available_files = [
        fname for fname in os.listdir(output_folder) if fname.rsplit(".", 4)[1] == "vie"
    ]

    corpus = [
        (file_name.rsplit(".", 4)[0], get_file(file_name))
        for file_name in available_files
    ]

    print("Corpus prepared with", len(corpus), "files")
    return np.array(corpus)


sentence_min_words = 5
sentence_word_limit = 30


def find_examples(ex_pattern, corpus, result_queue):
    """Find examples in the corpus that match the pattern. The examples should be put into the result_queue, as this is called from a sub-process.

    Parameters
    ----------
    ex_pattern : re.Pattern
        The pattern to match
    corpus : np.array
        The corpus to search in with tuples of (file_name, file_content)
    result_queue : AutoProxy[Queue]
        Multiprocessing Queue to put the results in
    """
    found_examples = []
    for file_name, file_content in corpus:
        for line in file_content:
            # Check case insensitive, and sentence should not go over word limit
            contains_word = ex_pattern.search(line)
            # Find start and end of match
            line_split = line.split()
            under_word_limit = len(line_split) < sentence_word_limit
            over_min_words = len(line_split) > sentence_min_words
            if contains_word and under_word_limit and over_min_words:
                start, end = ex_pattern.search(line).span()
                found_examples.append((file_name, line, len(line_split), start, end))

    result_queue.put(found_examples)


def process_mp(corpus_np, example, num_processes=6):
    # Create and start the processes
    processes = []
    split_size = len(corpus_np) // num_processes
    with Manager() as manager:
        result_queue = manager.Queue()

        ex_pattern = re.compile(rf"\b{example}\b", re.IGNORECASE)
        for i in range(num_processes):
            split_corpus = corpus_np[i * split_size : (i + 1) * split_size]
            print(f"Process {i}: Assigning corpus length", len(split_corpus))
            
            p = mp.Process(target=find_examples, args=(ex_pattern, split_corpus, result_queue))
            p.start()
            processes.append(p)

        # Wait for all processes to finish
        for p in processes:
            print("Waiting for process", p.pid)
            p.join()
        
        print("All processes finished")

        # Collect the results from the Queue and concatenate them into a single list
        final_result = []
        while not result_queue.empty():
            final_result.extend(result_queue.get())

    final_result = sorted(final_result, key=lambda x: x[2], reverse=True)
    return final_result


if __name__ == "__main__":
    corpus = prepare_corpus(output_folder)
    print("Total Examples", sum([len(c[1]) for c in corpus]))

    example = "cô gái"

    num_processes = 6

    print(process_mp(corpus, example, num_processes))
    print("Done")
