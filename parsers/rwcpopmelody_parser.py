#!/usr/bin/env python
"""
Translates the RWC-POP SMF (synchronized midi file) annotations to a set of
JAMS files, keeping only the melody track from each MIDI file.

The original data is described online at the following URL:
    https://staff.aist.go.jp/m.goto/RWC-MDB/rwc-mdb-p.html

To parse the entire dataset, you need to provide the path to two folders:
1. The folder containing the audio files, with filenames in the form
   RM-P[0-9]{3}*.wav from RM-P001*.wav to RM-P100*.wav
2. The folder containing the SMF files, with filenames in the form
   RM-P[0-9]{3}*.MID from RM-P001*.MID to RM-P100*.MID

Example:
./rwcpopmelody_parser.py ~/audio ~/AIST.RWC-MDB-P-2001.SMF_SYNC -o ~/RWC_POP_MELODY_jams/

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
import audioread

import jams


def get_track_duration(filename):
    '''Get the track duration for a filename'''
    with audioread.audio_open(filename) as fdesc:
        return fdesc.duration


def fill_file_metadata(jam, lab_file, duration):
    """Fills the global metada into the JAMS jam."""
    jam.file_metadata.artist = "TODO"
    jam.file_metadata.title = "TODO"
    jam.file_metadata.duration = duration


def fill_annotation_metadata(annot):
    """Fills the annotation metadata."""
    annot.annotation_metadata.corpus = "TODO"
    annot.annotation_metadata.version = "TODO"
    annot.annotation_metadata.annotation_tools = "TODO"
    annot.annotation_metadata.annotation_rules = "TODO"
    annot.annotation_metadata.validation = "TODO"
    annot.annotation_metadata.data_source = "TODO"
    annot.annotation_metadata.curator = jams.Curator(name="TODO",
                                                     email="TODO")
    annot.annotation_metadata.annotator = {}


def create_jams(lab_file, audio_file, out_file):
    """
    Creates a JAMS file given the RWC POP audio file (RM-P*.wav) and
    corresponding smf file (RM-P*.MID).
    Note: only the notes of the MELODY track are kept!
    """

    # TODO


def process_folder(audio_dir, smf_dir, out_dir):
    """Converts the original f0 annotations into the JAMS format, and saves
    them in the out_dir folder."""

    # TODO


def main():
    """Main function to convert the dataset into JAMS."""
    parser = argparse.ArgumentParser(
        description="Converts the RWC POP dataset to the JAMS format, keeping "
                    "only the notes of the melody track.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("audio_dir",
                        action="store",
                        help="RWC POP audio folder")
    parser.add_argument("smf_dir",
                        action="store",
                        help="RWC POP SMF folder")
    parser.add_argument("-o",
                        action="store",
                        dest="out_dir",
                        default="RWC_POP_MELODY_jams",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process_folder(args.audio_dir, args.smf_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds.", time.time() - start_time)

if __name__ == '__main__':
    main()
