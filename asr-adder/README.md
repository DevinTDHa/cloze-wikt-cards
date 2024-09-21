# Add Words Using Automatic Speech Recognition (ASR)

This folder contains a server and a client to record and extract vocabulary using ASR.

It contains a

1. Client GUI (Webpage) that lets users record audio and review the extracted vocabulary
2. A server that will host the website and do the transcribing using `vinai/PhoWhisper-medium`, a finetuned whisper model. Afterwards it will look up word sequential word combinations from the sentence to find the vocabulary.

## How to run

1. From this folder, run with `python server/server.py`. Then navigate to <http://localhost:5000> to access the webpage.
   - Note that currently this only works either locally or with an SSH tunnel.
