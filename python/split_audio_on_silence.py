#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Use pydub to split the WAV16 files along silence (<= -26.0 db) lasting >= 0.5 seconds."""

import argparse

from pathlib import Path
from subprocess import run
from multiprocessing import Pool

from pydub import AudioSegment
from pydub.silence import split_on_silence

parser = argparse.ArgumentParser(description="Specify whether to keep or delete source files.")
parser.add_argument("-k", "--keep_source")
args = parser.parse_args()
if args.keep_source:
   keepSource = False if args.keep_source == "0" else True
else:
   keepSource = True

def match_target_amplitude(aChunk, target_dBFS):
   """Normalize given audio chunk."""
   change_in_dBFS = target_dBFS - aChunk.dBFS
   return aChunk.apply_gain(change_in_dBFS)

def yieldInts():
   i = 0
   while True:
      yield i
      i += 1

# Make some silence for padding.
padding = AudioSegment.silent(duration=300)

# Define a function so we can use multiprocessing.
def splitWorksAudio(workPath):
   if workPath.is_dir():
      print(workPath)
      # Get the path to the source audio.
      sourceAudioPath = workPath / "source_audio"
      print(sourceAudioPath)
      # Restart the generator for each work.
      ints = yieldInts()

      # Get all the source audio files.
      for f in sorted(sourceAudioPath.iterdir()):
         if f.is_file():
            path = f.resolve()

            # Get the song and resample.
            if path.suffix == ".wav":
               song = AudioSegment.from_wav(str(path))
            elif path.suffix == ".mp3":
               song = AudioSegment.from_mp3(str(path))
            else:
               continue
            song = song.set_frame_rate(16000)

            # Make audio chunks.
            chunks = split_on_silence(
               song,
               silence_thresh=-50, # set dB considered as "silence"
               min_silence_len=500 # set length
            )

            # Process audio chunks.
            i = 0
            flag = False
            while i < len(chunks):
               chunk = chunks[i]
               if len(chunk) < 2000:
                  # Make long enough (>= 2s) to get something accurate from Julius.
                  i += 1
                  while len(chunk) < 2000 and i < len(chunks):
                     chunk += padding + chunks[i]
                     i += 1
                  flag = True

               audio_chunk = padding + chunk + padding
               # Normalize.
               normalized_chunk = match_target_amplitude(audio_chunk, -20.0)

               # Export.
               j = next(ints)
               exportDir = workPath / "split_audio"
               exportDir.mkdir(exist_ok=True)
               exportPath = (exportDir / f"{j:06}.wav").resolve()
               print("Exporting " + str(exportPath))
               normalized_chunk.export(str(exportPath), format="wav")

               if not flag:
                  i += 1
               flag = False

      if not keepSource:
         run(["rm", "-rf", str(sourceAudioPath.resolve())])

# Do this with multiprocessing so it's faster.
pool = Pool()
dataPath = Path("../data")
pool.map(splitWorksAudio, dataPath.iterdir())
pool.close()
pool.join()
