#!/usr/bin/env python
"""
Translates the MedleyDB Melody and Instrument Activation annotations to a set 
of JAMS files.

The original data is found online at the following URL:
    http://marl.smusic.nyu.edu/medleydb


Example:
./medleydb_parser.py MedleyDB/ [-o MedleyDB_JAMS/]

"""

__author__ = "Rachel M. Bittner"
__copyright__ = "Copyright 2014, Music and Audio Research Lab (MARL)"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "rachel.bittner@nyu.edu"

import argparse
import logging
import os
import time
import yaml
import pandas as pd

from tqdm import tqdm

import jams

from medleydb import __version__ as VERSION

CORPUS = "MedleyDB"


MEL1 = "The f0 curve of predominant melodic line drawn from a single source"
MEL2 = "The f0 curve of predominant melodic line drawn from multiple sources"
MEL3 = "The f0 curves of all melodic lines drawn from multiple sources"
MELODY_DEFS = {1: MEL1, 2: MEL2, 3: MEL3}


def fill_file_metadata(jam, artist, title, duration):
    """Fills the song-level metadata into the JAMS jam."""

    jam.file_metadata.artist = artist
    jam.file_metadata.title = title
    jam.file_metadata.duration = duration

def fill_genre_annotation_metadata(annot):
    """Fills the annotation metadata."""
    annot.annotation_metadata.corpus = CORPUS
    annot.annotation_metadata.version = VERSION
    annot.annotation_metadata.annotation_tools = ""
    annot.annotation_metadata.annotation_rules = ""
    annot.annotation_metadata.validation = "None"
    annot.annotation_metadata.data_source = "Manual Annotation"
    annot.annotation_metadata.curator = jams.Curator(name="Rachel Bittner",
                                                     email='rachel.bittner@nyu.edu')
    annot.annotation_metadata.annotator = {}


def fill_melody_annotation_metadata(annot, mel_type):
    """Fills the annotation metadata."""
    annot.annotation_metadata.corpus = CORPUS
    annot.annotation_metadata.version = VERSION
    annot.annotation_metadata.annotation_tools = "Tony"
    annot.annotation_metadata.annotation_rules = MELODY_DEFS[mel_type]
    annot.annotation_metadata.validation = "Manual Validation"
    annot.annotation_metadata.data_source = "Manual Annotation"
    annot.annotation_metadata.curator = jams.Curator(name="Rachel Bittner",
                                                     email='rachel.bittner@nyu.edu')
    annot.annotation_metadata.annotator = {}


def fill_instid_annotation_metadata(annot):
    """Fills the annotation metadata."""
    annot.annotation_metadata.corpus = CORPUS
    annot.annotation_metadata.version = VERSION
    annot.annotation_metadata.annotation_tools = ""
    annot.annotation_metadata.annotation_rules = ""
    annot.annotation_metadata.validation = "None"
    annot.annotation_metadata.data_source = "Automatic Annotation"
    annot.annotation_metadata.curator = jams.Curator(name="Juan P. Bello",
                                                     email='jpbello@nyu.edu')
    annot.annotation_metadata.annotator = {}


def fill_genre_annotation(genre):

    ann = jams.Annotation(namespace='tag_open')
    ann.append(time=0.0, duration=0.0, value=genre)
    fill_genre_annotation_metadata(ann)
    return ann

def fill_melody_annotation(annot_fpath, mel_type):
    """Fill a melody annotation with data from annot_fpath."""

    ann = jams.Annotation(namespace='pitch_hz')
    df = pd.read_csv(annot_fpath, header=None, names=['time', 'value'])
    df['duration'] = 0.0
    df['confidence'] = None

    ann.time = 0.0
    ann.duration = df['time'].max()

    ann.data = jams.JamsFrame.from_dataframe(df)

    fill_melody_annotation_metadata(ann, mel_type)

    return ann

def fill_instid_annotation(annot_fpath):
    """Fill an instrument id annotation with data from annot_fpath."""

    ann = jams.Annotation(namespace='tag_medleydb_instruments')
    df = pd.read_csv(annot_fpath)

    for _, record in df.iterrows():
        ann.append(time=record['start_time'],
                   duration=record['end_time'] - record['start_time'],
                   value=record['instrument_label'])
    ann.time = 0.0
    ann.duration = df['end_time'].max()

    fill_instid_annotation_metadata(ann)

    return ann

def create_JAMS(dataset_dir, trackid, out_file):
    """Creates a JAMS file given the Isophonics lab file."""

    metadata_file = os.path.join(dataset_dir, 'Audio', trackid, '{:s}_METADATA.yaml'.format(trackid))

    with open(metadata_file, 'r') as f_in:
        metadata = yaml.load(f_in)

    # New JAMS and annotation
    jam = jams.JAMS()


    # Create Genre Annotation
    jam.annotations.append(fill_genre_annotation(metadata['genre']))

    # Create Melody Annotations
    track_path = os.path.join(dataset_dir, 'Annotations', '{:s}_ANNOTATIONS'.format(trackid))

    melody1_fpath = os.path.join(track_path, "{:s}_MELODY1.csv".format(trackid))
    if os.path.exists(melody1_fpath):
        jam.annotations.append(fill_melody_annotation(melody1_fpath, 1))

    melody2_fpath = os.path.join(track_path, "{:s}_MELODY2.csv".format(trackid))
    if os.path.exists(melody2_fpath):
        jam.annotations.append(fill_melody_annotation(melody2_fpath, 2))

    # Create SourceID Annotation
    instid_fpath = os.path.join(track_path, "{:s}_SOURCEID.lab".format(trackid))

    if os.path.exists(instid_fpath):
        jam.annotations.append(fill_instid_annotation(instid_fpath))

    # Get the track duration
    duration = jam.annotations[-1].duration

    # Global file metadata
    fill_file_metadata(jam, metadata['artist'], metadata['title'], duration)

    # Save JAMS
    jam.save(out_file)


def process(in_dir, out_dir):
    """Converts MedleyDB Annotations into JAMS format, and saves
    them in the out_dir folder."""

    # Collect all trackid's.
    yaml_files = jams.util.find_with_extension(os.path.join(in_dir, 'Metadata'), 'yaml')
    trackids = [jams.util.filebase(y).replace("_METADATA", "") for y in yaml_files]

    jams.util.smkdirs(out_dir)

    for trackid in tqdm(trackids):
        jams_file = os.path.join(out_dir, "{:s}.jams".format(trackid))
        #Create a JAMS file for this track
        create_JAMS(in_dir, trackid, jams_file)


def main():
    """Main function to convert the dataset into JAMS."""
    parser = argparse.ArgumentParser(
        description="Converts the MARL-Chords dataset to the JAMS format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("in_dir",
                        action="store",
                        help="Isophonics main folder")
    parser.add_argument("-o",
                        action="store",
                        dest="out_dir",
                        default="outJAMS",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process(args.in_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds.", time.time() - start_time)

if __name__ == '__main__':
    main()
