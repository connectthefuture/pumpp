#!/usr/bin/env python
# -*- enconding: utf-8 -*-
'''Instantaneous event coding'''

import numpy as np

from .base import BaseTaskTransformer

__all__ = ['BeatTransformer']


class BeatTransformer(BaseTaskTransformer):
    '''Task transformation for beat tracking

    Attributes
    ----------
    name : str
        The name of this transformer

    sr : number > 0
        The audio sampling rate

    hop_length : int > 0
        The hop length for annotation frames
    '''
    def __init__(self, name='beat', sr=22050, hop_length=512):
        super(BeatTransformer, self).__init__(name=name,
                                              namespace='beat',
                                              sr=sr, hop_length=hop_length)

        self.register('beat', [None], np.bool)
        self.register('downbeat', [None], np.bool)
        self.register('mask_downbeat', [1], np.bool)

    def transform_annotation(self, ann, duration):
        '''Apply the beat transformer

        Parameters
        ----------
        ann : jams.Annotation
            The input annotation

        duration : number > 0
            The duration of the audio

        Returns
        -------
        data : dict
            data['beat'] : np.ndarray, shape=(n, 1)
                Binary indicator of beat/non-beat

            data['downbeat'] : np.ndarray, shape=(n, 1)
                Binary indicator of downbeat/non-downbeat

            mask_downbeat : bool
                True if downbeat annotations are present
        '''

        mask_downbeat = False

        intervals, values = ann.data.to_interval_values()
        values = np.asarray(values)

        beat_events = intervals[:, 0]
        beat_labels = np.ones((len(beat_events), 1))

        idx = (values == 1)
        if np.any(idx):
            downbeat_events = beat_events[idx]
            downbeat_labels = np.ones((len(downbeat_events), 1))
            mask_downbeat = True
        else:
            downbeat_events = np.zeros(0)
            downbeat_labels = np.zeros((0, 1))

        target_beat = self.encode_events(duration,
                                         beat_events,
                                         beat_labels)

        target_downbeat = self.encode_events(duration,
                                             downbeat_events,
                                             downbeat_labels)

        return {'beat': target_beat,
                'downbeat': target_downbeat,
                'mask_downbeat': mask_downbeat}
