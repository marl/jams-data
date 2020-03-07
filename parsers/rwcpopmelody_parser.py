#!/usr/bin/env python
"""
Translates the RWC-POP SMF (Synchronized Midi File) annotations to a set of
JAMS files, keeping only the melody track from each MIDI file.

The original dataset is described online at the following URL:
    https://staff.aist.go.jp/m.goto/RWC-MDB/rwc-mdb-p.html

To parse the entire dataset, you just need to provide the path to the folder
containing the SMF files, with filenames in the form RM-P[0-9]{3}*.MID from
RM-P001*.MID to RM-P100*.MID

Example:
./rwcpopmelody_parser.py ~/AIST.RWC-MDB-P-2001.SMF_SYNC -o ~/RWCPOP_melody_jams/

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


def fill_file_metadata(jam, metadata, n_track):
    """Fills the global metada into the JAMS jam."""
    jam.file_metadata.artist = metadata['Artist (Vocal)'][n_track]
    jam.file_metadata.title = metadata['Title'][n_track]

    d_str = metadata['Length'][n_track]
    jam.file_metadata.duration = (float(d_str.split(":")[0]) * 60 +
                                  float(d_str.split(":")[1]))

    # Store remaining RWC metadata in the sandbox
    sandbox_dict = {
        'Piece No.': metadata['Piece No.'][n_track],
        'Cat. Suffix': metadata['Cat. Suffix'][n_track],
        'Tr. No.': metadata['Tr. No.'][n_track],
        'Singer Information': metadata['Singer Information'][n_track],
        'Tempo': metadata['Tempo'][n_track],
        'Live Instruments Used': metadata['Live Instruments Used'][n_track],
        'Drum Information': metadata['Drum Information'][n_track]}

    jam.sandbox.update(**sandbox_dict)


def fill_annotation_metadata(annot):
    """Fills the annotation metadata."""
    annot.annotation_metadata.corpus = "RWC Music Database: Popular Music"
    annot.annotation_metadata.version = "1.0"
    annot.annotation_metadata.annotation_tools = ""
    annot.annotation_metadata.annotation_rules = ""
    annot.annotation_metadata.validation = ""
    annot.annotation_metadata.data_source = ""
    annot.annotation_metadata.curator = jams.Curator(name="Masataka Goto",
                                                     email="m.goto@aist.go.jp")
    annot.annotation_metadata.annotator = {}


def create_jams(smf_file, out_file, metadata):
    """
    Creates a JAMS file from an RWC POP smf file (RM-P*.MID).
    Note: only the notes of the MELODY track are kept!
    """

    # Load midi file
    m = midi.read_midifile(smf_file)

    # This will store the relevant MIDI tracks
    melody = []

    # Track 0 is metadata that we need
    melody.append(m[0])

    # Collect track text (convert to lower case and remove spaces)
    track_text = ["".join(e.text.lower().split()) for t in m
                  for e in t if isinstance(e, midi.TrackNameEvent)]

    assert len(track_text) == len(m)

    # Find the melody track: it should START with "melo", or if that's not
    # there then "voca" (for vocal).
    track_text = [t[:4] for t in track_text]
    if 'melo' in track_text:
        index = track_text.index('melo')
    elif 'voca' in track_text:
        index = track_text.index('voca')
    else:
        print("ABORTING TRACK: couldn't find melody for: %s" % smf_file)
        return 0

    melody.append(m[index])

    # Create new midi pattern with just these tracks
    m = midi.Pattern(tracks=melody, resolution=m.resolution,
                     format=m.format, tick_relative=m.tick_relative)

    # Write temporary midi file
    temp_midi = out_file.replace(".jams", ".temp.mid")
    midi.write_midifile(temp_midi, m)

    # Load temp midi file using pretty_midi
    pm = pretty_midi.PrettyMIDI(temp_midi)

    assert len(pm.instruments) == 2
    assert pm.instruments[0].notes == []
    assert len(pm.instruments[1].notes) > 0

    # Get the melody notes
    notes = pm.instruments[1].notes

    # Create jam
    jam = jams.JAMS()

    # Create annotation
    midi_ann = jams.Annotation('pitch_midi')

    # Add notes to the annotation
    for note in notes:
        midi_ann.append(time=note.start, duration=(note.end-note.start),
                        value=note.pitch, confidence=1.)

    # Fill annotation metadata
    fill_annotation_metadata(midi_ann)

    # Add annotation to jam
    jam.annotations.append(midi_ann)

    # Fill file metadata
    n_track = int(os.path.basename(smf_file)[4:7]) - 1
    fill_file_metadata(jam, metadata, n_track)

    # Save JAMS
    jam.save(out_file)

    # Remove temporary midi file
    os.remove(temp_midi)


def process_folder(smf_dir, out_dir):
    """Converts the original SMF annotations into the JAMS format (keeping only
    the notes of the melody track), and saves them in the out_dir folder."""

    # Collect all SMF annotations.
    smf_files = jams.util.find_with_extension(smf_dir, '.MID', depth=1)

    # Get metadata
    metadata = pd.read_csv('data/rwcmelodypop/metadata.csv')

    for smf in smf_files:

        jams_file = (
            os.path.join(out_dir,
                         os.path.basename(smf).replace('.MID', '.jams')))
        jams.util.smkdirs(os.path.split(jams_file)[0])
        # Create a JAMS file for this track
        create_jams(smf, jams_file, metadata)


def main():
    """Main function to convert the dataset into JAMS."""
    parser = argparse.ArgumentParser(
        description="Converts the RWC POP dataset to the JAMS format, keeping "
                    "only the notes of the melody track.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("smf_dir",
                        action="store",
                        help="RWC POP SMF folder")
    parser.add_argument("-o",
                        action="store",
                        dest="out_dir",
                        default="RWCPOP_melody_jams",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process_folder(args.smf_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds.", time.time() - start_time)

if __name__ == '__main__':
    main()
