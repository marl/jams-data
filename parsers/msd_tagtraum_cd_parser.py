#!/usr/bin/env python
"""
Converts a tagtraum MSD genre dataset into a collection of jams.

Datasets (msd_tagtraum_cd1.cls, msd_tagtraum_cd2.cls, msd_tagtraum_cd2c.cls)
are available from:

http://www.tagtraum.com/msd_genre_datasets.html

The files have to be unzipped.

Note that the tagtraum datasets do not contain artist and title
information and therefore have to be merged with the MSD
unique_tracks.txt file.

The file is available from:

http://labrosa.ee.columbia.edu/millionsong/sites/default/files/AdditionalFiles/unique_tracks.txt


If in the CD1 dataset two values are given, the first is assigned a
confidence of 2/3 and the second a confidence of 1/3 to reflect the votes
of the three source datasets CD1 was created from.

If only one value is present, the confidence is 1.

Confidence in CD2 follows a similar rule: If the two source datasets disagree, both
values are given a 1/2 confidence. If only one value is present, its confidence is 1.


Example for CD1:

./msd_tagtraum_cd_parser.py msd_tagtraum_cd1.cls unique_tracks.txt msd_tagtraum_cd1_jams

Example for CD2:

./msd_tagtraum_cd_parser.py msd_tagtraum_cd2.cls unique_tracks.txt msd_tagtraum_cd2_jams

"""

__author__ = "Hendrik Schreiber"
__copyright__ = "Copyright 2015, tagtraum industries incorporated"
__license__ = "MIT"
__version__ = "1.0"
__email__ = "hs@tagtraum.com"

import argparse
import logging
import os
import time

import jams


def fill_file_metadata(jam, artist, title, track_id):
    """Fills the global metada into the JAMS jam."""
    jam.file_metadata.artist = artist
    jam.file_metadata.duration = 0
    jam.file_metadata.title = title
    jam.file_metadata.identifiers = jams.Sandbox(msd_id=track_id)


def fix_genre_name(genre):
    """Normalize genre to all lowercase. Underscores are replaced with
    '/', as in Pop_Rock -> Pop/Rock. Leading/trailing whitespace is removed."""
    return genre.strip().lower().replace('_', '/')


def load_tagtraum_dataset(tagtraum_dataset):
    """Completely read tagtraum genre dataset into memory."""
    logging.info('Loading tagtraum dataset...')
    tagtraum_values = dict()
    genres = set()
    has_minority_genres = False
    for line in open(tagtraum_dataset):
        if not line.startswith('#'):
            # we have a valid line, let's split it
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                track_id = tokens[0]
                genre = fix_genre_name(tokens[1])
                tagtraum_values[track_id] = [genre]
                genres.add(genre)
            elif len(tokens) == 3:
                track_id = tokens[0]
                majority_genre = fix_genre_name(tokens[1])
                minority_genre = fix_genre_name(tokens[2])
                tagtraum_values[track_id] = [majority_genre, minority_genre]
                genres.add(majority_genre)
                genres.add(minority_genre)
                has_minority_genres = True
            else:
                logging.warning('Failed to parse tagtraum dataset line: {}'.format(line))

    logging.info('Loaded {} items.'.format(len(tagtraum_values)))

    return genres, has_minority_genres, tagtraum_values


def load_msd_metadata(msd_unique_tracks, tagtraum_values):
    """Reads unique tracks and saves artist/title tuple under
    track_id for those tracks that are in tagtraum_values."""
    logging.info('Matching with metadata from MSD unique tracks...')
    unique_tracks_values = dict()
    for line in open(msd_unique_tracks):
        # we have a valid line, let's split it
        tokens = line.strip().split('<SEP>')
        if len(tokens) == 4:
            track_id = tokens[0]
            artist = tokens[2]
            title = tokens[3]
            if track_id in tagtraum_values:
                unique_tracks_values[track_id] = (artist, title)
        else:
            logging.warning('Failed to parse unique tracks line: {}'.format(line))

    return unique_tracks_values


def process(tagtraum_dataset, msd_unique_tracks, out_dir):
    """Converts the original tagtraum genre annotations into the JAMS format,
    merges with MSD unique tracks, and saves them in the out_dir folder."""

    genres, has_minority_genres, tagtraum_values = load_tagtraum_dataset(tagtraum_dataset)
    unique_tracks_values = load_msd_metadata(msd_unique_tracks, tagtraum_values)

    # guess dataset based on number of genres and whether we found minority genres at all
    is_cd1 = len(genres) == 13
    is_cd2 = not is_cd1 and has_minority_genres

    # set namespace
    namespace = 'tag_msd_tagtraum_cd1' if is_cd1 else 'tag_msd_tagtraum_cd2'
    logging.info('Detected namespace "{}".'.format(namespace))

    # depending on the dataset, we have different confidence in the genre values
    majority_confidence = 2.0/3.0 if is_cd1 else 1.0/2.0
    minority_confidence = 1.0 - majority_confidence

    # set up meta stuff
    corpus = 'msd tagtraum cd1' if is_cd1 else ('msd tagtraum cd2' if is_cd2 else 'msd tagtraum cd2c')
    data_source = 'Top-MAGD, beaTunes, Last.fm' if is_cd1 else 'beaTunes, Last.fm'
    annotator = {'name': 'All Music Guide, Last.fm users, beaTunes users'} if is_cd1 else {'name': 'Last.fm users, beaTunes users'}
    curator = jams.Curator(name='Hendrik Schreiber',
                           email='hs@tagtraum.com')
    annotation_metadata = jams.AnnotationMetadata(curator=curator,
                                                  data_source=data_source,
                                                  version=1.0,
                                                  corpus=corpus,
                                                  annotator=annotator,
                                                  validation='Multiple data sources. Majority voting.')

    logging.info("Saving and validating JAMS...")

    for track_id, genres in tagtraum_values.iteritems():

        artist, title = unique_tracks_values[track_id]

        jam = jams.JAMS()

        # File meta data
        fill_file_metadata(jam, artist, title, track_id)

        # Create a new annotation object suitable for the dataset
        annotation = jams.Annotation(namespace=namespace)

        # Figure out confidence
        confidence = 1.0 if len(genres) == 1 else majority_confidence

        # Append majority vote
        annotation.data.add_observation(value=genres[0], confidence=confidence, time=0, duration=0)

        # Append minority vote, if available
        if len(genres) == 2:
            annotation.data.add_observation(value=genres[1], confidence=minority_confidence, time=0, duration=0)

        jam.annotations.append(annotation)

        # Add Metadata
        jam.annotations[-1].annotation_metadata = annotation_metadata

        # Write file
        out_file = os.path.join(out_dir, track_id[2:3], track_id[3:4], track_id[4:5], track_id + '.jams')
        jams.util.smkdirs(os.path.split(out_file)[0])
        jam.save(out_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Converts the tagtraum genre annotations for MSD to the JAMS format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("tagtraum_dataset",
                        action="store",
                        help="tagtraum genre dataset file")
    parser.add_argument("msd_unique_tracks",
                        action="store",
                        default="unique_tracks.txt",
                        help="MSD unique tracks file")
    parser.add_argument("out_dir",
                        action="store",
                        default="outJAMS",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process(args.tagtraum_dataset, args.msd_unique_tracks, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds." % (time.time() - start_time))
