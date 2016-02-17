#!/usr/bin/env python
"""
Translates the LabROSA MIREX2005 melody f0 training data annotations to a set
of JAMS files.

The original data is found online at the following URL:
    http://www.ee.columbia.edu/~graham/mirex_melody/mirex05TrainFiles.zip

To parse the entire dataset, you simply need to provide the path to the
unarchived folder.

Example:
./mirex05melody_parser.py ~/mirex05TrainFiles -o ~/mirex05TrainFiles_jams/

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
    jam.file_metadata.artist = ""
    jam.file_metadata.title = os.path.basename(lab_file).replace("REF.txt", "")
    jam.file_metadata.duration = duration


def fill_annotation_metadata(annot):
    """Fills the annotation metadata."""
    annot.annotation_metadata.corpus = "MIREX05"
    annot.annotation_metadata.version = "1.0"
    annot.annotation_metadata.annotation_tools = ""
    annot.annotation_metadata.annotation_rules = ""
    annot.annotation_metadata.validation = ""
    annot.annotation_metadata.data_source = ""
    annot.annotation_metadata.curator = jams.Curator(name="Daniel P.W. Ellis",
                                                     email="dpwe"
                                                           "@ee.columbia.edu")
    annot.annotation_metadata.annotator = {}


def create_JAMS(lab_file, audio_file, out_file):
    """
    Creates a JAMS file given the MIREX05 annotation file (*REF.txt) and
    the corresponding audio file (*.wav).
    """

    # Import melody annotation
    jam, melody_ann = jams.util.import_lab('pitch_hz', lab_file)

    # Fill annotation metadata
    fill_annotation_metadata(melody_ann)

    # Fill file metadata
    duration = get_track_duration(audio_file)
    fill_file_metadata(jam, lab_file, duration)

    # Save JAMS
    jam.save(out_file)


def process_folder(in_dir, out_dir):
    """Converts the original f0 annotations into the JAMS format, and saves
    them in the out_dir folder."""

    # Collect all melody f0 annotations.
    f0_files = jams.util.find_with_extension(in_dir, '.txt', depth=1)

    for f0_file in f0_files:
        audio_file = f0_file.replace("REF.txt", ".wav")
        jams_file = os.path.join(out_dir,
                            os.path.basename(f0_file).replace('.txt', '.jams'))
        jams.util.smkdirs(os.path.split(jams_file)[0])
        # Create a JAMS file for this track
        create_JAMS(f0_file, audio_file, jams_file)


def main():
    """Main function to convert the dataset into JAMS."""
    parser = argparse.ArgumentParser(
        description="Converts the LabROSA mirex05 training dataset to the JAMS"
                    " format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("in_dir",
                        action="store",
                        help="mirex05TrainFiles main folder")
    parser.add_argument("-o",
                        action="store",
                        dest="out_dir",
                        default="mirex05TrainFiles_jams",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process_folder(args.in_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds.", time.time() - start_time)

if __name__ == '__main__':
    main()
