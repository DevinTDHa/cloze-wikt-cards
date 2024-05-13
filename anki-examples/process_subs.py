from tqdm import tqdm
import pandas as pd
import os
import zipfile
import regex
from wtpsplit import WtP


def check_if_file_exists_in_output_folder(file_name):
    return file_name in output_files


def get_sub_list(subs_folder):
    # TODO: somehow theres still duplicates?
    all_files = os.listdir(subs_folder)

    subs_list = set()

    for file_name in all_files:
        file_split = file_name.rsplit(".", 4)
        if len(file_split) != 5:
            continue

        base_name, lang, _, _, _ = file_split

        if lang != "vie":
            continue
        if base_name not in subs_list:
            subs_list.add(file_name)

    return sorted(list(subs_list))


def find_srt_name(zip_ref):
    for file in zip_ref.namelist():
        if file.endswith(".srt"):
            return file
    return None


def find_line_endings(txt):
    if "\r\n" in txt[:100]:
        return "\r\n\r\n"
    else:
        return "\n\n"


def process_zip_file(zip_file, wtp):
    out_file_name = os.path.splitext(os.path.basename(zip_file))[0] + ".txt"
    out_path = os.path.join(output_folder, out_file_name)

    if check_if_file_exists_in_output_folder(out_file_name):
        print("File already processed: ", out_file_name)
        return None

    def process_line(line, seperator):
        line_split = line.split(seperator) 
        if len(line_split) < 3:
            return ""
        _, _, src = line.split(seperator)[:3]
        processed = src.strip(" -\n\r\t")  # Trailing chars
        processed = regex.sub(r"<[^>]*?>", "", processed)  # Remove HTML tags
        processed = regex.sub(
            r"[^\p{L}\p{N}\p{P}\p{Z}]", "", processed
        )  # Remove non-letter, non-number, non-punctuation, non-separator chars

        return processed

    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        srt_name = find_srt_name(zip_ref)
        if srt_name:
            with zip_ref.open(srt_name) as srt_file:
                contents = srt_file.read().decode("utf-8", errors="ignore")
                line_endings = find_line_endings(contents)
                contents_parsed = [
                    process_line(line, line_endings[:2])
                    for line in contents.split(line_endings)
                ]
        else:
            print("SRT file not found in the zip file.")
            return None

    content_text_only = " ".join(contents_parsed)
    splits = wtp.split(content_text_only, lang_code="vi")

    # write to csv file with the same name
    with open(out_path, "w") as f:
        f.write("\n".join(splits))
    print("processed file: ", out_path)


if __name__ == "__main__":
    subs_folder = "/media/ducha/SSDSHARED/VN/subs_dump/viet_subs_raw/viet_subs"
    output_folder = "/media/ducha/SSDSHARED/VN/subs_dump/viet_subs_processed2"
    os.makedirs(output_folder, exist_ok=True)
    # Treat files in output_folder as cache
    output_files = set(os.listdir(output_folder))

    subs_list = get_sub_list(subs_folder)

    wtp = WtP("wtp-bert-mini")
    wtp.to("cuda")

    with open("error_files.txt", "w+") as ef:
        with tqdm(total=len(subs_list)) as pbar:
            for file in tqdm(subs_list):
                try:
                    process_zip_file(os.path.join(subs_folder, file), wtp)
                    pbar.set_postfix({"status": "O"})
                except Exception as e:
                    print("Error processing file: ", file)
                    ef.write(file + "\n" + str(e) + "\n\n")
                    pbar.set_postfix({"status": "X"})
                pbar.update(1)
