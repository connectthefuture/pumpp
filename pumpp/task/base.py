#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''The base class for task transformer objects'''

import numpy as np
from librosa import time_to_frames
import jams

from ..base import Scope

__all__ = ['BaseTaskTransformer']


def fill_value(dtype):
    '''Get a fill-value for a given dtype

    Parameters
    ----------
    dtype : type

    Returns
    -------
    `np.nan` if `dtype` is real or complex

    0 otherwise
    '''
    if np.issubdtype(dtype, np.float) or np.issubdtype(dtype, np.complex):
        return dtype(np.nan)

    return dtype(0)


class BaseTaskTransformer(Scope):
    '''Base class for task transformer objects

    Attributes
    ----------
    name : str
        The name prefix for this transformer object

    namespace : str
        The JAMS namespace for annotations in this task

    sr : number > 0
        The sampling rate for audio

    hop_length : int > 0
        The number of samples between frames
    '''

    def __init__(self, name, namespace, sr, hop_length):
        super(BaseTaskTransformer, self).__init__(name)

        # This will trigger an exception if the namespace is not found
        jams.schema.is_dense(namespace)

        self.namespace = namespace
        self.sr = sr
        self.hop_length = hop_length

    def empty(self, duration):
        '''Create an empty jams.Annotation for this task.

        This method should be overridden by derived classes.

        Parameters
        ----------
        duration : int >= 0
            Duration of the annotation
        '''
        return jams.Annotation(namespace=self.namespace, time=0, duration=0)

    def transform(self, jam, query=None):
        '''Transform jam object to make data for this task

        Parameters
        ----------
        jam : jams.JAMS
            The jams container object

        query : string, dict, or callable [optional]
            An optional query to narrow the elements of `jam.annotations`
            to be considered.

            If not provided, all annotations are considered.

        Returns
        -------
        data : dict
            A dictionary of transformed annotations.
            All annotations which can be converted to the target namespace
            will be converted.
        '''
        anns = []
        if query:
            results = jam.search(**query)
        else:
            results = jam.annotations

        # Find annotations that can be coerced to our target namespace
        for ann in results:
            try:
                anns.append(jams.nsconvert.convert(ann, self.namespace))
            except jams.NamespaceError:
                pass

        duration = jam.file_metadata.duration

        # If none, make a fake one
        if not anns:
            anns = [self.empty(duration)]

        # Apply transformations
        results = []
        for ann in anns:

            results.append(self.transform_annotation(ann, duration))
            # If the annotation range is None, it spans the entire track
            if ann.time is None or ann.duration is None:
                valid = [0, duration]
            else:
                valid = [ann.time, ann.time + ann.duration]

            results[-1]['_valid'] = time_to_frames(valid, sr=self.sr,
                                                   hop_length=self.hop_length)

        # Prefix and collect
        return self.merge(results)

    def encode_events(self, duration, events, values, dtype=np.bool):
        '''Encode labeled events as a time-series matrix.

        Parameters
        ----------
        duration : number
            The duration of the track

        events : ndarray, shape=(n,)
            Time index of the events

        values : ndarray, shape=(n, m)
            Values array.  Must have the same first index as `events`.

        dtype : numpy data type

        Returns
        -------
        target : ndarray, shape=(n_frames, n_values)
        '''

        # FIXME: support sparse encoding
        frames = time_to_frames(events, sr=self.sr,
                                hop_length=self.hop_length)

        n_total = int(time_to_frames(duration, sr=self.sr,
                                     hop_length=self.hop_length))

        target = np.empty((n_total, values.shape[1]), dtype=dtype)

        target.fill(fill_value(dtype))
        values = values.astype(dtype)
        for column, event in zip(values, frames):
            target[event] += column

        return target

    def encode_intervals(self, duration, intervals, values, dtype=np.bool):
        '''Encode labeled intervals as a time-series matrix.

        Parameters
        ----------
        duration : number
            The duration (in frames) of the track

        intervals : np.ndarray, shape=(n, 2)
            The list of intervals

        values : np.ndarray, shape=(n, m)
            The (encoded) values corresponding to each interval

        dtype : np.dtype
            The desired output type

        Returns
        -------
        target : np.ndarray, shape=(duration * sr / hop_length, m)
            The labeled interval encoding, sampled at the desired frame rate
        '''
        frames = time_to_frames(intervals, sr=self.sr,
                                hop_length=self.hop_length)

        n_total = int(time_to_frames(duration, sr=self.sr,
                                     hop_length=self.hop_length))

        values = values.astype(dtype)

        target = np.empty((n_total, values.shape[1]), dtype=dtype)

        target.fill(fill_value(dtype))

        for column, interval in zip(values, frames):
            target[interval[0]:interval[1]] += column

        return target
