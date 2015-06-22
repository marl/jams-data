#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# CREATED:2015-06-22 13:05:41 by Brian McFee <brian.mcfee@nyu.edu>
'''Parse CAL10K annotation data into JAMS format'''

import sys
import argparse
import os

import audioread
import pandas as pd
import jams

__curator__ = dict(name='Derek Tingle')
__corpus__ = 'CAL10K'


def get_track_duration(filename):
    '''Get the track duration for a filename'''
    with audioread.audio_open(filename) as fdesc:
        return fdesc.duration


def load_tags(tag_file, song_table):
    
    tags = pd.DataFrame(index=song_table.index)
    
    with open(tag_file, 'r') as fdesc:
        for line in fdesc:
            
            key, rest = line.split('\t', 1)
            rest = [int(x) for x in rest.split('\t')[::2]]
            tags[key] = pd.Series(index=rest, data=True, name=key)
            
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

    print 'Saving {:s}'.format(outfile)
    jam.save(outfile)


def process_track(input_dir, output_dir, metadata, tags, compress):


    # Construct track metadata
    duration = get_track_duration(os.path.join(input_dir,
                                               'audio',
                                               metadata['filename']))

    file_meta = jams.FileMetadata(title=metadata['title'],
                                  artist=metadata['artist'],
                                  duration=duration,
                                  identifiers=jams.Sandbox(id=metadata.name))


    # Get the tag annotation
    amd = jams.AnnotationMetadata(curator=jams.Curator(**__curator__),
                                  corpus=__corpus__)

    ann = jams.Annotation('tag_cal10k', annotation_metadata=amd)

    for tag in tags:
        ann.append(time=0, duration=duration, value=tag)

    jam = jams.JAMS(file_metadata=file_meta)
    jam.annotations.append(ann)
    jam.sandbox.content_path = metadata['filename']

    save_jam(output_dir, jam, metadata.name, compress)
    

def parse_cal10k(input_dir=None, output_dir=None, compress=False):
    '''Convert CAL10K to jams format'''

    # First, get the song list
    songs = pd.read_table(os.path.join(input_dir, 'songList.tab'),
                          header=None, index_col=0,
                          names=['artist', 'title', 'filename'])

    # Then, get the tag assignments
    tag_matrix = load_tags(os.path.join(input_dir, 'PandoraTagSong.tab'),
                           songs)

    # Finally, build out the JAMS list
    for song_id, metadata in songs.iterrows():
        process_track(input_dir,
                      output_dir,
                      metadata,
                      tag_matrix.loc[song_id].dropna().index,
                      compress)


def parse_arguments(args):

    parser = argparse.ArgumentParser(description='CAL10K tag parser')

    parser.add_argument('input_dir',
                        type=str,
                        help='Path to the CAL10K root directory')

    parser.add_argument('output_dir',
                        type=str,
                        help='Path to output jam files')

    parser.add_argument('-z', '--zip', dest='compress', 
                        action='store_true', help='Compress jams output')

    return vars(parser.parse_args(args))


if __name__ == '__main__':
    parameters = parse_arguments(sys.argv[1:])

    parse_cal10k(**parameters)

