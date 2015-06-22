#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# CREATED:2015-06-22 15:10:37 by Brian McFee <brian.mcfee@nyu.edu>
'''Parse CAL500 annotation data into JAMS format'''

from __future__ import print_function

import sys
import argparse
import os

import audioread
import pandas as pd
import jams

__curator__ = dict(name='Doug Turnbull')
__corpus__ = 'CAL500'


def get_track_duration(filename):
    '''Get the track duration for a filename'''
    with audioread.audio_open(filename) as fdesc:
        return fdesc.duration


def load_tags(input_dir, songs):
    hard_csv = pd.read_csv(os.path.join(input_dir, 'hardAnnotations.txt'), header=None)
    soft_csv = pd.read_csv(os.path.join(input_dir, 'softAnnotations.txt'), header=None)

    tags = hard_csv * soft_csv
    tags.index = songs['track']

    vocab = pd.read_table(os.path.join(input_dir, 'vocab.txt'),
                         header=None,
                         names=['tag'])

    tags.columns = vocab['tag']

    return tags



def save_jam(output_dir, jam, id_num, compress):
    '''Save the output jam'''

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if compress:
        outfile = os.extsep.join([str(id_num), 'jamz'])
    else:
        outfile = os.extsep.join([str(id_num), 'jams'])

    outfile = os.path.join(output_dir, outfile)

    print('Saving {:s}'.format(outfile))
    jam.save(outfile)


def process_track(input_dir, output_dir, metadata, tags, compress):


    # Construct track metadata
    duration = get_track_duration(os.path.join(input_dir,
                                               'mp3',
                                               os.path.extsep.join([metadata['track'],
                                               'mp3'])))

    artist, title = metadata['track'].split('-', 1)

    file_meta = jams.FileMetadata(title=title,
                                  artist=artist,
                                  duration=duration)

    # Get the tag annotation
    amd = jams.AnnotationMetadata(curator=jams.Curator(**__curator__),
                                  corpus=__corpus__)

    ann = jams.Annotation('tag_cal500', annotation_metadata=amd)

    for value, confidence in tags.iteritems():
        ann.append(time=0,
                   duration=duration,
                   value=value,
                   confidence=confidence)

    jam = jams.JAMS(file_metadata=file_meta)
    jam.annotations.append(ann)
    jam.sandbox.content_path = metadata['track']

    save_jam(output_dir, jam, metadata.name, compress)


def parse_cal500(input_dir=None, output_dir=None, compress=False):
    '''Convert CAL500 to jams format'''

    # First, get the song list
    songs = pd.read_table(os.path.join(input_dir, 'songNames.txt'),
                          header=None, names=['track'])

    # Then, get the tag assignments
    tag_matrix = load_tags(input_dir, songs)

    # Finally, build out the JAMS list
    for _, metadata in songs.iterrows():
        song_id = metadata['track']
        try:
            process_track(input_dir,
                          output_dir,
                          metadata,
                          tag_matrix.loc[song_id][tag_matrix.loc[song_id].nonzero()[0]],
                          compress)

        except IOError as exc:
            print('Could not process file: {:s}, skipping.'.format(song_id))



def parse_arguments(args):

    parser = argparse.ArgumentParser(description='CAL500 tag parser')

    parser.add_argument('input_dir',
                        type=str,
                        help='Path to the CAL500 root directory')

    parser.add_argument('output_dir',
                        type=str,
                        help='Path to output jam files')

    parser.add_argument('-z', '--zip', dest='compress', 
                        action='store_true', help='Compress jams output')

    return vars(parser.parse_args(args))


if __name__ == '__main__':
    parameters = parse_arguments(sys.argv[1:])

    parse_cal500(**parameters)

