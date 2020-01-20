#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__ = "Classes for New CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import numpy

try:
    from PySide import QtCore
    import FreeCAD
    import Plot
    withinFreeCAD = True
except:
    withinFreeCAD = False
    import matplotlib
    matplotlib.use("svg")
    import matplotlib.pyplot as plt
    print(plt.get_backend())  #TkAgg
    import matplotlib.animation as animation


''' this class can only process velocity and pressure residues, pyFoam has already got this function
backends: matplotlib (with or without FreeCAD), gnuplot (should be phrased out)
matplotlib is not working within FreeCAD, because matplotlib using PyQt eventloop, same as FreeCAD will freeze GUI
Instead, Plot module of FreeCAD should be used
matplotlib standalone mode is not yet working
'''
class FoamResidualPloter():
    def __init__(self, backend = 'matplotlib'):
        self.reset()
        if backend == 'gnuplot':
            import Gnuplot
            self.g = Gnuplot.Gnuplot()
            self.g('set style data lines')
            self.g.title("Simulation residuals")
            self.g.xlabel("Iteration")
            self.g.ylabel("Residual")

            self.g("set grid")
            self.g("set logscale y")
            self.g("set yrange [0.95:1.05]")
            self.g("set xrange [0:1]")
        elif backend == 'matplotlib':
            if withinFreeCAD:
                self.fig = Plot.figure(FreeCAD.ActiveDocument.Name + "Residuals")
                self.Timer = QtCore.QTimer()
                self.Timer.timeout.connect(self.refresh)
                self.Timer.start(1000)
                self.updated = False
            else:
                self.fig = plt.figure()
                self.axis = self.fig.add_subplot(1,1,1)
                self.axis.set_title("Simulation residuals")
                self.axis.set_xlabel("Iteration")
                self.axis.set_ylabel("Residual")
                self.axis.grid(True)
                self.axis.set_yscale('log')
                self.axis.set_ylim(1e-4, 1e2)  # or autoscale?
                #xaxis data is not needed for steady case
                for var in self.residuals:
                    self.axis.plot(self.residuals[var], label = var)
                plt.legend()
                #todo: setup animation hook
        else:
            print('plot backend {} is not supported'.format(backend))
        self.backend = backend

    def refresh(self):  ## only for matplotlib in FreeCAD plot module
        if self.updated:
            self.updated = False
            ax = self.fig.axes
            ax.cla()
            ax.set_title("Simulation residuals")
            ax.set_xlabel("Iteration")
            ax.set_ylabel("Residual")

            ax.plot(self.UxResiduals, label="$U_x$", color='violet', linewidth=1)
            ax.plot(self.UyResiduals, label="$U_y$", color='green', linewidth=1)
            ax.plot(self.UzResiduals, label="$U_z$", color='blue', linewidth=1)
            ax.plot(self.pResiduals, label="$p$", color='orange', linewidth=1)

            ax.grid()
            ax.set_yscale('log')
            ax.legend()

        self.fig.canvas.draw()

    def reset(self):
        # set init values for plotting tool independent data, gnuplot does not accept numpy.array?
        init_residual = [1]  # numpy.array([1])
        self.UxResiduals = init_residual
        self.UyResiduals = init_residual
        self.UzResiduals = init_residual
        self.pResiduals = init_residual
        self.residuals = {'xVelocity': self.UxResiduals, 'yVelocity': self.UyResiduals, 'zVelocity':self.UzResiduals, 'pressure': self.pResiduals}
        self.niter = 0

    def process_text(self, text):
        loglines = text.split('\n')
        printlines = []
        for line in loglines:
            # print line,
            split = line.split()

            # Only store the first residual per timestep
            if line.startswith(u"Time = "):
                self.niter += 1

            # print split,  Uz does not exist for 2D case, continuity is important but not yet extracted
            if "Ux," in split and self.niter > len(self.UxResiduals):
                self.UxResiduals.append(float(split[7].split(',')[0]))
            if "Uy," in split and self.niter > len(self.UyResiduals):
                self.UyResiduals.append(float(split[7].split(',')[0]))
            if "Uz," in split and self.niter > len(self.UzResiduals):
                self.UzResiduals.append(float(split[7].split(',')[0]))
            if "p," in split and self.niter > len(self.pResiduals):
                self.pResiduals.append(float(split[7].split(',')[0]))
        self.updated = True

    def plot(self):
        if self.backend == 'gnuplot':
            # NOTE: the mod checker is in place for the possibility plotting takes longer
            # NOTE: than a small test case to solve
            import Gnuplot
            if numpy.mod(self.niter, 1) == 0:
                self.g.plot(Gnuplot.Data(self.UxResiduals, with_='line', title="Ux", inline=1),
                            Gnuplot.Data(self.UyResiduals, with_='line', title="Uy", inline=1),
                            Gnuplot.Data(self.UzResiduals, with_='line', title="Uz", inline=1),
                            Gnuplot.Data(self.pResiduals, with_='line', title="p"))

            if self.niter >= 2:
                self.g("set autoscale")  # NOTE: this is just to supress the empty yrange error when GNUplot autscales
        elif self.backend == 'matplotlib':  ## only for matplotlib NOT in FreeCAD plot module
            if not withinFreeCAD:
                if self.niter%5==0:  #only re-plot some data points
                    self.axis.clear()
                    for var in self.residuals:
                        self.axis.plot(self.residuals[var], label = var)
        else:
            print('plot backend {} is not supported'.format(backend))