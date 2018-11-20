#!/usr/bin/env python
"""
This script parses the HEMAN dataset into the JAMS format.

Usage example:
    ./heman_parser.py heman_data/ output_heman_jams
"""

import argparse
import glob
import logging
import os
import pickle
import time

import jams

__author__ = "Oriol Nieto"
__license__ = "MIT"
__version__ = "1.1"
__email__ = "oriol@nyu.edu"


def create_jams(song_title):
    """Creates the JAMS object."""
    jam = jams.JAMS()
    jam.file_metadata.duration = 1    # All symbolic
    jam.file_metadata.artist = ""     # TODO
    jam.file_metadata.title = song_title
    return jam


def create_annotation(ann, ann_id):
    """Creates the annotation object."""
    pattern_ann = jams.Annotation(namespace='pattern_jku')

    # Metadata
    pattern_ann.annotation_metadata.corpus = "HEMAN"
    pattern_ann.annotation_metadata.annotator = ann_id
    pattern_ann.annotation_metadata.curator = jams.Curator(
        name="Iris Yuping Ren", email="yuping.ren.iris@gmail.com")
    pattern_ann.annotation_metadata.version = "1.1"

    # Data
    pattern_id = 1
    for confidence in ann.keys():
        for pattern in ann[confidence]:
            for onset, pitch in pattern:
                val = {
                    "pattern_id": pattern_id,
                    "midi_pitch": pitch,
                    "morph_pitch": pitch,
                    "staff": 1,
                    "occurrence_id": 1  # TODO
                }
                dur = 1  # TODO
                pattern_ann.append(time=onset, duration=dur, value=val,
                                   confidence=confidence)
            pattern_id += 1

    return pattern_ann


def parse_song(song_file, out_dir):
    """Parses a single song contained in the given pickle file and
    places it in the output dir."""
    with open(song_file, "rb") as f:
        song = pickle.load(f)

    song_title = os.path.splitext(os.path.basename(song_file))[0]
    jam = create_jams(song_title)
    for ann_id in song.keys():
        pattern_ann = create_annotation(song[ann_id], ann_id)
        jam.annotations.append(pattern_ann)

    out_file = os.path.join(out_dir, song_title + ".jams")
    jam.save(out_file)


def process(in_dir, out_dir):
    """Converts the original HEMAN files into the JAMS format, and saves
    them in the out_dir folder."""

    # Check if output folder and create it if needed:
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Do one song at a time
    song_files = glob.glob(os.path.join(in_dir, "*.pkl"))
    for song_file in song_files:
        parse_song(song_file, out_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Converts the HEMAN dataset to the JAMS format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("in_dir",
                        action="store",
                        help="HEMAN main folder")
    parser.add_argument("out_dir",
                        action="store",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process(args.in_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds." % (time.time() - start_time))
