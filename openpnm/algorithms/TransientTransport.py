import numpy as np
import scipy.sparse as sprs
from openpnm.algorithms import GenericTransport
from openpnm.core import logging
logger = logging.getLogger(__name__)


class TransientTransport(GenericTransport):
    r"""
    A subclass of GenericTransport to perform transient and steady simulations.
    """

    def __init__(self, **kwargs):
        self.settings.update({})
        super().__init__(**kwargs)

    def set_IC(self, values):
        r"""
        """
        if (type(values) == float or type(values) == int):
            self[self.settings['quantity']] = values * np.ones(
                                              shape=(self.Np, ), dtype=float)

    def update_A(self):
        r"""
        """
        network = self.project.network
        phase = self.project.phases()[self.settings['phase']]
        md = phase[self.settings['molar_density']][0]
        Vi = md*network['pore.volume']
        dt = self.settings['t_step']
        s = self.settings['t_scheme']
        if (s == 'implicit'):
            f1, f2 = 1, 1
        elif (s == 'cranknicolson'):
            f1, f2 = 0.5, 1
        elif (s == 'steady'):
            f1, f2 = 1, 0
        # Compute A (operations involve conversion to 'csr')
        A = ((f2/dt) * sprs.coo_matrix.multiply(
            sprs.coo_matrix(np.reshape(Vi, (self.Np, 1)), shape=(self.Np,)),
            sprs.identity(self.Np, format='coo')) + f1 * self._A_steady)
        # Convert A to 'coo' format to apply BCs
        A = sprs.coo_matrix(A)
        self.A = A
        return A

    def update_b(self):
        r"""
        """
        network = self.project.network
        phase = self.project.phases()[self.settings['phase']]
        md = phase[self.settings['molar_density']][0]
        Vi = md*network['pore.volume']
        dt = self.settings['t_step']
        s = self.settings['t_scheme']
        if (s == 'implicit'):
            f1, f2, f3 = 1, 1, 0
        elif (s == 'cranknicolson'):
            f1, f2, f3 = 0.5, 1, 0
        elif (s == 'steady'):
            f1, f2, f3 = 1, 0, 1
        x_old = self[self.settings['quantity']]
        b = (f2*(1-f1)*(-self._A_steady)*x_old +
             f2*(Vi/dt)*x_old +
             f3*np.zeros(shape=(self.Np, ), dtype=float))
        self.b = b
        return b

    def setup(self):
        r"""
        """
        # Create a scratch b from IC to apply BCs to A matrix
        self.b = self[self.settings['quantity']]
        self.apply_BCs()
        # Save A matrix (with BCs applied) of the steady sys of eqs
        self._A_steady = self.A
        # Override A and b according to t_scheme and apply BCs
        self.update_A()
        self.update_b()
        self.apply_BCs()

    def run(self, t=None):
        r"""
        """
        print('―'*80)
        print('Running TransientTransport')
        self.setup()
        if t is None:
            t = self.settings['t_initial']
        self._run_transient(t=t)

    def _run_transient(self, t):
        tf = self.settings['t_final']
        dt = self.settings['t_step']
        to = self.settings['t_output']
        tol = self.settings['tolerance']
        s = self.settings['t_scheme']
        res = 1  # Initialize the residual

        # Make sure 'tf' and 'to' are multiples of 'dt'
        tf = tf + (dt-(tf % dt))*((tf % dt) != 0)
        to = to + (dt-(to % dt))*((to % dt) != 0)
        self.settings['t_final'] = tf
        self.settings['t_output'] = to
        outputs = np.append(np.arange(t+to, tf, to), tf)

        # Export the initial field (t=t_initial)
        self[self.settings['quantity']+'_initial'] = (
                                            self[self.settings['quantity']])

        if (s == 'steady'):  # If solver in steady mode, do one iteration
            print('    Running in steady mode')
            x_new = self._solve()
            self[self.settings['quantity']] = x_new

        else:  # Do time iterations
            for time in np.arange(t+dt, tf+dt, dt):
                if (res >= tol):  # Check if the steady state is reached
                    print('    Current time step: '+str(time)+' s')
                    x_old = self[self.settings['quantity']]
                    x_new = self._solve()
                    # Compute the residual
                    res = np.amax(np.absolute(x_new[x_new != 0] -
                                              x_old[x_new != 0]) /
                                  np.absolute(x_new[x_new != 0]))
                    print('        Residual: '+str(res))
                    self[self.settings['quantity']] = x_new
                    # Output transient solutions
                    if time in outputs:
                        self[self.settings['quantity'] +
                             str(np.where(outputs == time)[0][0])] = x_new
                        print('        Exporting time step: '+str(time)+' s')
                    self.update_b()
                    self.apply_BCs()
                else:  # Stop time iterations if residual < tolerance
                    self[self.settings['quantity'] + '_steady'] = x_new
                    print('        Exporting time step: '+str(time)+' s')
                    break
            if (time == tf):
                print('    Maximum time step reached: '+str(time)+' s')
            else:
                print('    Transient solver converged after: '+str(time)+' s')
