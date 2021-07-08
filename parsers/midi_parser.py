#!/usr/bin/env python
"""
Translates any folder of MIDI files to a set of JAMS files.

To parse the MIDI files, you just need to provide the path to the folder
containing the files.

Example:
./midi_parser.py ~/midi_files -o ~/midi_jams/

NOTE: pitch bend information is ignored, so notes with pitch bends will be
converted to notes with a fixed pitch value.

"""

__author__ = "J. Salamon"
__copyright__ = "Copyright 2016, Music and Audio Research Lab (MARL)"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "justin.salamon@nyu.edu"

import argparse
import logging
import os
import time
import midi
import pretty_midi
import pandas as pd

import jams


def fill_file_metadata(jam, midi_file, duration):
    """Fills the global metada into the JAMS jam."""
    jam.file_metadata.title = os.path.basename(midi_file)[:-4]
    jam.file_metadata.duration = duration


def fill_annotation_metadata(annot):
    """Fills the annotation metadata."""
    annot.annotation_metadata.corpus = ""
    annot.annotation_metadata.version = ""
    annot.annotation_metadata.annotation_tools = ""
    annot.annotation_metadata.annotation_rules = ""
    annot.annotation_metadata.validation = ""
    annot.annotation_metadata.data_source = ""
    annot.annotation_metadata.curator = jams.Curator(name="",
                                                     email="")
    annot.annotation_metadata.annotator = {}


def create_jams(midi_file, out_file):
    """
    Creates a JAMS file from a MIDI file
    """

    # Create jam
    jam = jams.JAMS()

    # Create annotation
    midi_ann = jams.Annotation('pitch_midi')

    # Load midi file
    pm = pretty_midi.PrettyMIDI(midi_file)

    notes = []

    for inst in pm.instruments:
        for note in inst.notes:
            midi_ann.append(time=note.start, duration=(note.end-note.start),
                            value=note.pitch, confidence=1.)

    # Fill annotation metadata
    fill_annotation_metadata(midi_ann)

    # Add annotation to jam
    jam.annotations.append(midi_ann)

    # Fill file metadata
    duration = pm.get_end_time()
    fill_file_metadata(jam, midi_file, duration)

    # Save JAMS
    jam.save(out_file)


def process_folder(midi_dir, out_dir):
    """Converts the original SMF annotations into the JAMS format (keeping only
    the notes of the melody track), and saves them in the out_dir folder."""

    # Collect all MIDI annotations.
    midi_files = jams.util.find_with_extension(midi_dir, '.mid', depth=1)
    midi_files.extend(jams.util.find_with_extension(midi_dir, '.MID', depth=1))
    print(len(midi_files))

    for mf in midi_files:

        jams_file = (
            os.path.join(out_dir, os.path.basename(mf)[:-3] + "jams"))
        jams.util.smkdirs(os.path.split(jams_file)[0])
        # Create a JAMS file for this track
        print(mf)
        create_jams(mf, jams_file)


def main():
    """Main function to convert the dataset into JAMS."""
    parser = argparse.ArgumentParser(
        description="Converts a dataset of MIDI files to the JAMS format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("midi_dir",
                        action="store",
                        help="Folder of MIDI files")
    parser.add_argument("-o",
                        action="store",
                        dest="out_dir",
                        default="midi_jams",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process_folder(args.midi_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds.", time.time() - start_time)

if __name__ == '__main__':
    main()
