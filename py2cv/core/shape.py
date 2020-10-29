# -*- coding: utf-8 -*-

############################################################################
#
#   Copyright (C) 2008-2015
#    Christian Kohlöffel
#    Vinzenz Schulz
#    Jean-Paul Schouwstra
#
#   This file is part of DXF2GCODE.
#
#   DXF2GCODE is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   DXF2GCODE is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with DXF2GCODE.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

from __future__ import absolute_import
from __future__ import division

from math import radians, pi
import logging

import py2cv.globals.globals as g
from py2cv.core.point import Point
from py2cv.core.linegeo import LineGeo

from PyQt5 import QtCore

logger = logging.getLogger("Core.Shape")


class Shape(object):

    """
    The Shape Class includes all plotting, GUI functionality and export functions
    related to the Shapes.
    """
    # only need default arguments here because of the change of usage with
    # super in QGraphicsItem

    def __init__(self, nr=-1, closed=True, parentEntity=None, geos=[]):
        if nr == -1:
            return

        self.type = "Shape"
        self.nr = nr
        self.closed = closed
        self.cut_cor = 40
        self.parentEntity = parentEntity
        self.parentLayer = None
        self.geos = Geos(geos)

        self.cw = True

        self.stmove = None

        self.send_to_TSP = g.config.vars.Route_Optimisation['default_TSP']

        self.selected = False
        self.disabled = False
        self.allowedToChange = True

        # preset defaults
        self.axis3_start_mill_depth = g.config.vars.Depth_Coordinates[
            'axis3_start_mill_depth']
        self.axis3_slice_depth = g.config.vars.Depth_Coordinates[
            'axis3_slice_depth']
        self.axis3_mill_depth = g.config.vars.Depth_Coordinates[
            'axis3_mill_depth']
        self.f_g1_plane = g.config.vars.Feed_Rates['f_g1_plane']
        self.f_g1_depth = g.config.vars.Feed_Rates['f_g1_depth']
        # Parameters for drag knife
        self.drag_angle = radians(
            g.config.vars.Drag_Knife_Options['drag_angle'])

    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """

        logger.debug(self.closed)
        return "\nnr:          %i" % self.nr +\
               "\nclosed:      %s" % self.closed +\
               "\ngeos:        %s" % self.geos

    def tr(self, string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string
        @return: the translated unicode string if it was possible to translate
        """
        return str(QtCore.QCoreApplication.translate("Shape",
                                                           string_to_translate))

    def setSelected(self, flag=False):
        self.selected = flag

    def isSelected(self):
        return self.selected

    def setDisable(self, flag=False):
        self.disabled = flag

    def isDisabled(self):
        return self.disabled

    def setToolPathOptimized(self, flag=False):
        self.send_to_TSP = flag

    def isToolPathOptimized(self):
        return self.send_to_TSP

    def isDirectionOfGeosCCW(self, geos):
        pass

    def AnalyseAndOptimize(self):
        self.setNearestStPoint(Point())
        logger.debug(
            self.tr("Analysing the shape for CW direction Nr: %s" % self.nr))

        if self.isDirectionOfGeosCCW(self.geos):
            self.reverse()
            logger.debug(self.tr("Had to reverse the shape to be CW"))
        self.cw = True

    def setNearestStPoint(self, stPoint):
        if self.closed:
            logger.debug(self.tr("Clicked Point: %s" % stPoint))
            start = self.get_start_end_points(True)
            logger.debug(self.tr("Old Start Point: %s" % start))

            min_geo_nr, _ = min(enumerate(self.geos.abs_iter()),
                                key=lambda geo:
                                geo[1].get_start_end_points(True).distance(stPoint))

            # Overwrite the geometries in changed order.
            self.geos = Geos(self.geos[min_geo_nr:] + self.geos[:min_geo_nr])

            start = self.get_start_end_points(True)
            logger.debug(self.tr("New Start Point: %s" % start))
        elif len (self.geos) > 0:
            # if shape is not closed, we can just select between start and end points
            dist1 = self.geos.abs_el(0).get_start_end_points(True).distance(stPoint)
            dist2 = self.geos.abs_el(-1).get_start_end_points(False).distance(stPoint)
            if dist2 < dist1:
                self.reverse()

    def reverse(self, geos=None):
        if not geos:
            geos = self.geos
        geos.reverse()
        for geo in geos:
            geo.reverse()
        self.cw = not self.cw

    def switch_cut_cor(self):
        """
        Switches the cutter direction between 41 and 42.

        G41 = Tool radius compensation left.
        G42 = Tool radius compensation right
        """
        if self.cut_cor == 41:
            self.cut_cor = 42
        elif self.cut_cor == 42:
            self.cut_cor = 41

    def append(self, geo):
        geo.make_abs_geo(self.parentEntity)
        self.geos.append(geo)

    def get_start_end_points_physical(self, start_point=None, angles=None):
        """
        With multiple slices end point could be start point.
        e.g. useful for the optimal rout etc
        """
        if start_point or self.closed:
            return self.get_start_end_points(start_point, angles)
        else:
            max_slice = max(self.axis3_slice_depth,
                            self.axis3_mill_depth -
                            self.axis3_start_mill_depth)
            if max_slice == 0:
                end_should_be_start = True
            else:
                end_should_be_start = (
                    self.axis3_start_mill_depth - self.axis3_mill_depth) // max_slice % 2 == 0
            if not end_should_be_start:
                return self.get_start_end_points(start_point, angles)
            else:
                start_stuff = self.get_start_end_points(True, angles)
                if angles is False:
                    end_stuff = start_stuff[0], -start_stuff[1]
                else:
                    end_stuff = start_stuff
                if start_point is None:
                    return start_stuff, end_stuff
                else:
                    return end_stuff

    def get_start_end_points(self, start_point=None, angles=None):
        if start_point is None:
            return (self.geos.abs_el(0).get_start_end_points(True, angles),
                    self.geos.abs_el(-1).get_start_end_points(False, angles))
        elif start_point:
            return self.geos.abs_el(0).get_start_end_points(True, angles)
        else:
            return self.geos.abs_el(-1).get_start_end_points(False, angles)

    def make_path(self, drawHorLine, drawVerLine):
        pass

    def calc_bounding_box(self):
        """
        Calculated the BoundingBox of the geometry and saves it into self.BB
        """
        self.BB = self.geos.abs_el(0).BB
        for geo in self.geos.abs_iter():
            self.BB = self.BB.joinBB(geo.BB)

    def make_shape_ccw(self):
        """
        This method is called after the shape has been generated before it gets
        plotted to change all shape direction to a CW shape.
        """

        if not(self.closed):
            return

        # Optimization for closed shapes
        # Start value for the first sum

        if self.isDirectionOfGeosCCW(self.geos):
            self.reverse()
            logger.debug(self.tr("Had to reverse the shape to be CW"))
        self.cw = True

    def isHit(self, xy, tol):
        if self.BB.Ps.x - tol <= xy.x <= self.BB.Pe.x + tol\
                and self.BB.Ps.y - tol <= xy.y <= self.BB.Pe.y + tol:
            for geo in self.geos.abs_iter():
                if geo.isHit(self, xy, tol):
                    return True
        return False

    def Write_GCode_for_geo(self, geo, PostPro):
        pass

    def Write_GCode(self, PostPro):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of the shape.
        @param PostPro: this is the Postprocessor class including the methods
        to export
        """
        if g.config.machine_type == 'drag_knife':
            return self.Write_GCode_Drag_Knife(PostPro)

        prv_cut_cor = self.cut_cor
        if (self.cut_cor != 40 and
                not g.config.vars.Cutter_Compensation["done_by_machine"]):
            self.cut_cor = 40
            new_geos = Geos(self.stmove.geos[1:])
        else:
            new_geos = self.geos

        # If there is nothing to export
        if len(new_geos) == 0:
            return ""

        new_geos = PostPro.breaks.getNewGeos(new_geos)
        # initialisation of the string
        exstr = ""

        # Get the mill settings defined in the GUI
        safe_retract_depth = self.parentLayer.axis3_retract
        safe_margin = self.parentLayer.axis3_safe_margin

        max_slice = self.axis3_slice_depth
        workpiece_top_Z = self.axis3_start_mill_depth
        # We want to mill the piece, even for the first pass, so remove one
        # "slice"
        initial_mill_depth = workpiece_top_Z - abs(max_slice)
        depth = self.axis3_mill_depth
        f_g1_plane = self.f_g1_plane
        f_g1_depth = self.f_g1_depth

        # Save the initial Cutter correction in a variable
        has_reversed = False

        # If the Output Format is DXF do not perform more then one cut.
        if PostPro.vars.General["output_type"] == 'dxf':
            depth = max_slice

        if max_slice == 0 and g.config.machine_type != 'lasercut':
            logger.error(self.tr("ERROR: Z infeed depth is null!"))

        if initial_mill_depth < depth:
            logger.warning(self.tr(
                "WARNING: initial mill depth (%i) is lower than end mill depth (%i). Using end mill depth as final depth.") % (
                initial_mill_depth, depth))

            # Do not cut below the depth.
            initial_mill_depth = depth

        mom_depth = initial_mill_depth

        # Move the tool to the start.
        if self.cut_cor == 40:#Fix G40 G00 Position Bug
            self.stmove.geos.abs_el(0).x = new_geos[0].Ps.x
            self.stmove.geos.abs_el(0).y = new_geos[0].Ps.y

        exstr += self.stmove.geos.abs_el(0).Write_GCode(PostPro)

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_pre_shape_cut()

        # Cutter radius compensation when G41 or G42 is on, AND cutter
        # compensation option is set to be done outside the piece
        if self.cut_cor != 40 and PostPro.vars.General["cc_outside_the_piece"]:
            exstr += PostPro.set_cut_cor(self.cut_cor)

            exstr += PostPro.chg_feed_rate(f_g1_plane)
            exstr += self.stmove.geos.abs_el(1).Write_GCode(PostPro)
            exstr += self.stmove.geos.abs_el(2).Write_GCode(PostPro)

        if g.config.machine_type != 'lasercut':
            exstr += PostPro.rap_pos_z(
                workpiece_top_Z + abs(safe_margin))  # Compute the safe margin from the initial mill depth
            exstr += PostPro.chg_feed_rate(f_g1_depth)
            exstr += PostPro.lin_pol_z(mom_depth)
            exstr += PostPro.chg_feed_rate(f_g1_plane)

        # Cutter radius compensation when G41 or G42 is on, AND cutter
        # compensation option is set to be done inside the piece
        if self.cut_cor != 40 and not PostPro.vars.General["cc_outside_the_piece"]:
            exstr += PostPro.set_cut_cor(self.cut_cor)

            exstr += self.stmove.geos.abs_el(1).Write_GCode(PostPro)
            exstr += self.stmove.geos.abs_el(2).Write_GCode(PostPro)

        # Write the geometries for the first cut
        for geo in new_geos.abs_iter():
            exstr += self.Write_GCode_for_geo(geo, PostPro)

        # Turning the cutter radius compensation
        if self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]:
            exstr += PostPro.deactivate_cut_cor()

        # Numbers of loops
        snr = 0
        # Loops for the number of cuts
        while mom_depth > depth and max_slice != 0.0:
            snr += 1
            mom_depth = mom_depth - abs(max_slice)
            if mom_depth < depth:
                mom_depth = depth

            # Erneutes Eintauchen
            exstr += PostPro.chg_feed_rate(f_g1_depth)
            exstr += PostPro.lin_pol_z(mom_depth)
            exstr += PostPro.chg_feed_rate(f_g1_plane)

            # If it is not a closed contour
            if not self.closed:
                self.reverse(new_geos)
                self.switch_cut_cor()
                # switch the "reversed" state (in order to restore it at the
                # end)
                has_reversed = not has_reversed

                # If cutter radius compensation is turned on. Turn it off - because some interpreters cannot handle
                # a switch
                if self.cut_cor != 40 and not PostPro.vars.General["cancel_cc_for_depth"]:
                    exstr += PostPro.deactivate_cut_cor()
                    exstr += PostPro.set_cut_cor(self.cut_cor)


            # If cutter correction is enabled
            if self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]:
                exstr += PostPro.set_cut_cor(self.cut_cor)

            for geo in new_geos.abs_iter():
                exstr += self.Write_GCode_for_geo(geo, PostPro)

            # Turning off the cutter radius compensation if needed
            if self.cut_cor != 40 and PostPro.vars.General["cancel_cc_for_depth"]:
                exstr += PostPro.deactivate_cut_cor()

        if g.config.machine_type != 'lasercut':
            # Do the tool retraction
            exstr += PostPro.chg_feed_rate(f_g1_depth)
            exstr += PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
            exstr += PostPro.rap_pos_z(safe_retract_depth)

        # If cutter radius compensation is turned on.
        if self.cut_cor != 40 and not PostPro.vars.General["cancel_cc_for_depth"]:
            exstr += PostPro.deactivate_cut_cor()

        # Initial value of direction restored if necessary
        if has_reversed:
            self.reverse(new_geos)
            self.switch_cut_cor()

        self.cut_cor = prv_cut_cor

        # Add string to be added before the shape will be cut.
        exstr += PostPro.write_post_shape_cut()

        return exstr

    def Write_GCode_Drag_Knife(self, PostPro):
        pass

    def join_colinear_lines(self):
        pass


class Geos(list):

    def __init__(self, *args):
        list.__init__(self, *args)

    def abs_iter(self):
        for geo in list.__iter__(self):
            yield geo.abs_geo if geo.abs_geo else geo


    def abs_el(self, element):
        return self[element].abs_geo if self[element].abs_geo else self[element]
