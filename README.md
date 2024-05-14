# anki-examples

Finds examples for you Anki Vocabulary Cards, based on a local directory of example files.

```
$ python fill_examples.py /media/subs_dump/viet_subs_processed $CSV_PATH

Preparing corpus from /media/subs_dump/viet_subs_processed
Corpus prepared with 13646 files
Total Examples 7736833


Missing Examples   : 163
Vietnamese word    : chủ động
English translation: active

Found 228 total examples, showing the first 10.
Choose an example to add (0-9) or press 'r' to shuffle and refresh the list, 'z' to undo or 's' to skip:
0. star.trek.s01.e20.court.martial.(... : sau đó là chủ động không thích Chờ chút, tôi không hiểu cô.
1. monster.(2018)                   ... : Cậu Cruz, cậu đã thú nhận với cảnh sát là cậu chủ động tham gia Vâng, đúng ạ.
2. elite.s04.e03.when.lies.dance.wit... : Tức là em đã chủ động làm tới?
3. american.horror.story.s01.e08.rub... : Anh ta chủ động Hay bị động trên giường?
4. so.not.worth.it.s01.e08.episode.1... : Em phải chủ động hỏi à?
5. le.chant.du.loup.(2019)          ... : Và sonar chủ động thứ dữ.
6. ho.ching.2.(2014)                ... : Tôi thậm chí không biết là người nữ cũng có thể chủ động.
7. the.last.kingdom.s04.e02.episode.... : Ta đang chủ động, không phải hắn.
8. mine.s01.e09.a.toast.to.the.devil... : Còn nữa, đừng chủ động gọi tôi.
9. the.morning.show.s02.e01.my.least... : Đôi khi, cô phải chủ động để các lá bài thể hiện Ồ.
Your choice: 
```

What you need:

1. A folder of text files, where each line is an example sentence
2. A CSV with vocabulary for Anki with three columns:
   1. target language
   2. translation
   3. Example

## Requirements

TODO

## Running the Script

Navigate to `anki-examples` and run the `fill_examples.py` script with your folder of examples and your current csv:

```bash
python fill_examples.py $CORPUS_FOLDER $CSV_PATH
```

The resulting filled csv will be saved to `$CSV_PATH_filled.csv`.
If it already exists, this will be loaded instead at the start.
