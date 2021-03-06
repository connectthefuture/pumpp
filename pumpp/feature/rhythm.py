#!/usr/bin/env python
'''Rhythm analysis features'''

import numpy as np
from librosa import fmt
from librosa.feature import tempogram

from .base import FeatureExtractor

__all__ = ['Tempogram', 'TempoScale']


class Tempogram(FeatureExtractor):
    '''Tempogram: the short-time autocorrelation of the accent signal

    Attributes
    ----------
    name : str
        The name of this feature extractor

    sr : number > 0
        The sampling rate of audio

    hop_length : int > 0
        The hop length of analysis windows

    win_length : int > 0
        The length of the analysis window (in frames)
    '''
    def __init__(self, name, sr, hop_length, win_length):
        super(Tempogram, self).__init__(name, sr, hop_length)

        self.win_length = win_length

        self.register('tempogram', [None, win_length], np.float32)

    def transform_audio(self, y):
        '''Compute the tempogram

        Parameters
        ----------
        y : np.ndarray
            Audio buffer

        Returns
        -------
        data : dict
            data['tempogram'] : np.ndarray, shape=(n_frames, win_length)
                The tempogram
        '''
        tgram = tempogram(y=y, sr=self.sr,
                          hop_length=self.hop_length,
                          win_length=self.win_length).astype(np.float32)

        return {'tempogram': tgram.T}


class TempoScale(Tempogram):
    '''Tempogram scale transform.

    Mellin scale transform magnitude of the Tempogram.

    Attributes
    ----------
    name : str
        Name of this extractor

    sr : number > 0
        Sampling rate of audio

    hop_length : int > 0
        Hop length for analysis frames

    win_length : int > 0
        Number of frames per analysis window

    n_fmt : int > 0
        Number of scale coefficients to retain
    '''
    def __init__(self, name, sr, hop_length, win_length, n_fmt=128):
        super(TempoScale, self).__init__(name, sr, hop_length, win_length)

        self.n_fmt = n_fmt
        self.pop('tempogram')
        self.register('temposcale', [None, 1 + n_fmt // 2], np.float32)

    def transform_audio(self, y):
        '''Apply the scale transform to the tempogram

        Parameters
        ----------
        y : np.ndarray
            The audio buffer

        Returns
        -------
        data : dict
            data['temposcale'] : np.ndarray, shape=(n_frames, n_fmt)
                The scale transform magnitude coefficients
        '''
        data = super(TempoScale, self).transform_audio(y)
        data['temposcale'] = np.abs(fmt(data.pop('tempogram'),
                                        axis=1,
                                        n_fmt=self.n_fmt)).astype(np.float32)
        return data
