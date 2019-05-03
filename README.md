# Japanese Text Utilities

This repository provides some utilities developed for working with Japanese text. They were originally part of a larger project on voice synthesis and recognition in Japanese. None of the files have been edited for their inclusion here and users are expected to edit files as necessary for their own purposes. The sub-goal of this part of the project was to locate the source text of an utterance, _i.e._, to find the sentence in the text file which the volunteer had just spoken.

## Scraping

The script `scrape.py` uses the [LibriVox](https://librivox.org/) [API](https://librivox.org/api/info) in order to find Japanese texts that have been performed by volunteers (a set of sound and text files is referred to as a _work_). The sound files are downloaded, along with the raw text, which is often from [Aozora Bunko](https://www.aozora.gr.jp/). Unfortunately, the LibriVox API is not well-maintained and does not, as of 03 May 2019, provide a way find all works in a particular language. To compensate for this, we use a heuristic based on the total number of works in LibriVox and simply loop through a sufficient number of IDs. This probably misses some works and suggestions/pull requests to remedy this are welcomed. For later examination, JSON files containing data on the work are saved in the work's directory, as are pickle files of the scraped IDs, _etc_. Besides the LibriVox API, help is also provided by [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).

## Normalization

After works are downloaded, the scripts `xml_to_text.py`, `create_mappings.py` and `normalize.py` are used to render them in an acceptable format for text processing. Firstly, Aozora Bunko's XML tags are stripped from the works, leaving only the surface forms. There are some caveats: older (now non-standard) surface forms are preserved, but their readings may be obscure to the modern reader; some surface forms are not representable with modern fonts (_kyūjitai_, _etc_.) and here Aozora Bunko may embed small image files that are deleted during cleaning (_cf_. [_Kumonoito_ by Akutagawa](https://www.aozora.gr.jp/cards/000879/files/92_14545.html)).

For normalization, we have `create_mappings.py` and `normalize.py`. The aim of the first file is to create character mappings so that we can easily replace

- full-width alphanumeric characters with their half-width equivalents (this also operates on some punctuation and other symbols),
- half-width _katakana_ and other Japanese symbols to full-width Japanese,
- punctuation to `\u0020` (an ASCII space) (this particular mapping is over-zealous and removes historical _etc_. punctuation).

If you wish to edit this file, make sure your editor is capable of displaying Unicode, otherwise there will be plenty of [_mojibaké_](https://en.wikipedia.org/wiki/Mojibake) (not as tasty as it sounds). Although creating them doesn't take particularly long, pickle files of the mappings are saved so that we can simply load them and save precious time instead.

The second file cumulates in a function imaginatively called `normalizeSentence()` which takes a sentence and applies certain regexes and the above mappings to produce a normalized sentence. This includes removing all characters not used in ASCII or typically in Japanese (useful for stripping place names in their native language from Wikipedia articles, for example) and removing duplicate and unnecessary whitespace.

## Transcribing sound files with [Julius](https://github.com/julius-speech/julius)

The next step is to take sound files from LibriVox and split them into little chunks, roughly corresponding to clauses in the original text. We use James Robert's [Pydub](https://github.com/jiaaro/pydub) to split up sound files along silences of adequate length. If sound files are not long enough, transcription is impossible, so we ensure a minimum length. The file is `split_on_audio.py`.

Once sound files have been made, they are saved in the correct format (WAV) for processing and lists of the files to be processed are created with `make_filelist.py`.

We then begin the transcription process by running Nagoya Institute of Technology's [Julius](https://github.com/julius-speech/julius) utility in server mode on ports `20000` and up, one file per port. The file is `serve_julius.py`. Each instance of Julius takes a list of files as input and, once connected to, will begin transcribing the files and will output the results as XML. Unfortunately, the XML is not well-formed and so some massaging is required to allow [lxml](https://lxml.de) to parse it. The binary files required by Julius are large and cannot be committed to GitHub, but would be located in `./julius/`. They are available through the link above.

Connecting to the Julius servers and yielding the transcriptions are performed by `call_julius.py`. This script also performs the aforementioned massaging. Transcriptions are saved in SQLite databases in the corresponding work's folder.

## Matching transcriptions to text

The file `fuzzy_match.py` attempts to find candidate matches of transcriptions and source text. It does this by using [MeCab](https://taku910.github.io/mecab/)'s (developed by Kyoto University Graduate School of Informatics)  _wakati_ and _yomi_ parsers to perform a combined surface form and pronunciation comparison. In short, good candidates for a transcription are things that "sort of look the same" and "sort of sound the same". The comparison is simply a weighted sum of these two criteria, which is judged as "good" if it passes some threshold. The scores for each criterion are generated using [Levenshtein distances](https://en.wikipedia.org/wiki/Levenshtein_distance) as calculated by SeatGeek's [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy) package.

Candidate source text sentences are then saved in the SQLite databases mentioned above. This file is the least polished of all of them and should be regarded as unstable.

## Further work

- Refine the fuzzy matching algorithm to actually be good and not be bad.
- Ensure that we are indeed scraping all Japanese works from LibriVox.
- Find all Japanese works in the public domain available on Aozora Bunko and scrape and normalize them as well.
