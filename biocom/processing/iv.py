"""Linear current-voltage relationship model.

Provides a simple linearized I-V model for predicting I-V responses around
an operating point.
"""

import numpy as np
from numpy import ndarray
from typing import Union

class LinearIV(object):
    """Linear current-voltage relationship model.
    
    Models I-V behavior as linear around an operating point, useful for
    predicting AC current/voltage responses.
    
    :param i_mid: Operating point current in A
    :type i_mid: float
    :param v_mid: Operating point voltage in V
    :type v_mid: float
    :param dvdi: Differential resistance (dV/dI) in Ohm
    :type dvdi: float
    
    :ivar i_mid: Operating point current
    :ivar v_mid: Operating point voltage
    :ivar dvdi: Differential resistance
    """
    def __init__(self, i_mid: float, v_mid: float, dvdi: float):
        self.i_mid = i_mid
        self.v_mid = v_mid
        self.dvdi = dvdi
    
    def eval_v(self, i: Union[float, ndarray]) -> Union[float, ndarray]:
        """Evaluate voltage for given current.
        
        :param i: Current value(s) in A
        :type i: Union[float, ndarray]
        :return: Voltage value(s) in V
        :rtype: Union[float, ndarray]
        """
        if not np.isscalar(i):
            i = np.asarray(i)
        return self.v_mid + (i - self.i_mid) * self.dvdi


    def eval_i(self, v: Union[float, ndarray]):
        """Evaluate current for given voltage.
        
        :param v: Voltage value(s) in V
        :type v: Union[float, ndarray]
        :return: Current value(s) in A
        :rtype: Union[float, ndarray]
        """
        if not np.isscalar(v):
            v = np.asarray(v)
        return self.i_mid + (v - self.v_mid) * self.dvdi ** -1


    def _eval_ac(self, s_dc: float, s_ac: float, output: str):
        out = getattr(self, f'eval_{output}')(np.array([s_dc - s_ac, s_dc, s_dc + s_ac]))
        out_dc = out[1]
        out_ac = abs(out[-1] - out[0]) / 2
        
        return out_dc, out_ac
        
    def eval_iac(self, v_dc: float, v_ac: float):
        """Evaluate AC current response to AC voltage perturbation.
        
        :param v_dc: DC voltage in V
        :type v_dc: float
        :param v_ac: AC voltage amplitude in V
        :type v_ac: float
        :return: Tuple of (i_dc, i_ac) in A
        :rtype: Tuple[float, float]
        """
        return self._eval_ac(v_dc, v_ac, 'i')
    
    def eval_vac(self, i_dc: float, i_ac: float):
        """Evaluate AC voltage response to AC current perturbation.
        
        :param i_dc: DC current in A
        :type i_dc: float
        :param i_ac: AC current amplitude in A
        :type i_ac: float
        :return: Tuple of (v_dc, v_ac) in V
        :rtype: Tuple[float, float]
        """
        return self._eval_ac(i_dc, i_ac, 'v')
        