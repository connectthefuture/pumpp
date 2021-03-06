#!/usr/bin/env python
"""STFT feature extractors"""

import numpy as np
import librosa

from .base import FeatureExtractor, phase_diff

__all__ = ['STFT', 'STFTMag', 'STFTPhaseDiff']


class STFT(FeatureExtractor):
    '''Short-time Fourier Transform (STFT) with both magnitude
    and phase.

    Attributes
    ----------
    name : str
        The name of this transformer

    sr : number > 0
        The sampling rate of audio

    hop_length : int > 0
        The hop length of STFT frames

    n_fft : int > 0
        The number of FFT bins per frame

    See Also
    --------
    STFTMag
    STFTPhaseDiff
    '''
    def __init__(self, name, sr, hop_length, n_fft):
        super(STFT, self).__init__(name, sr, hop_length)

        self.n_fft = n_fft

        self.register('mag', [None, 1 + n_fft // 2], np.float32)
        self.register('phase', [None, 1 + n_fft // 2], np.float32)

    def transform_audio(self, y):
        '''Compute the STFT magnitude and phase.

        Parameters
        ----------
        y : np.ndarray
            The audio buffer

        Returns
        -------
        data : dict
            data['mag'] : np.ndarray, shape=(n_frames, 1 + n_fft//2)
                STFT magnitude

            data['phase'] : np.ndarray, shape=(n_frames, 1 + n_fft//2)
                STFT phase
        '''
        mag, phase = librosa.magphase(librosa.stft(y,
                                                   hop_length=self.hop_length,
                                                   n_fft=self.n_fft,
                                                   dtype=np.float32))
        return {'mag': mag.T, 'phase': np.angle(phase.T)}


class STFTPhaseDiff(STFT):
    '''STFT with phase differentials

    See Also
    --------
    STFT
    '''
    def __init__(self, *args, **kwargs):
        super(STFTPhaseDiff, self).__init__(*args, **kwargs)
        phase_field = self.pop('phase')
        self.register('dphase', phase_field.shape, phase_field.dtype)

    def transform_audio(self, y):
        '''Compute the STFT with phase differentials.

        Parameters
        ----------
        y : np.ndarray
            the audio buffer

        Returns
        -------
        data : dict
            data['mag'] : np.ndarray, shape=(n_frames, 1 + n_fft//2)
                The STFT magnitude

            data['dphase'] : np.ndarray, shape=(n_frames, 1 + n_fft//2)
                The unwrapped phase differential
        '''
        data = super(STFTPhaseDiff, self).transform_audio(y)
        data['dphase'] = phase_diff(data.pop('phase'), axis=0)
        return data


class STFTMag(STFT):
    '''STFT with only magnitude.

    See Also
    --------
    STFT
    '''
    def __init__(self, *args, **kwargs):
        super(STFTMag, self).__init__(*args, **kwargs)
        self.pop('phase')

    def transform_audio(self, y):
        '''Compute the STFT

        Parameters
        ----------
        y : np.ndarray
            The audio buffer

        Returns
        -------
        data : dict
            data['mag'] : np.ndarray, shape=(n_frames, 1 + n_fft//2)
                The STFT magnitude
        '''
        data = super(STFTMag, self).transform_audio(y)
        data.pop('phase')

        return data
