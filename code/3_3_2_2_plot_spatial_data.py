import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from osgeo import ogr
import numpy as np


try:
    numeric_types = (int, float, long)
except NameError:
    numeric_types = (int, float)


class SimpleVectorPlotter(object):
    """Plots vector data represented as lists of coordinates."""

    # _graphics = {}

    def __init__(self, interactive, ticks=False, figsize=None, limits=None):
        """Construct a new SimpleVectorPlotter.

        interactive - boolean flag denoting interactive mode
        ticks       - boolean flag denoting whether to show axis tickmarks
        figsize     - optional figure size
        limits      - optional geographic limits (x_min, x_max, y_min, y_max)
        """
        # if figsize:
        #     plt.figure(num=1, figsize=figsize)
        plt.figure(num=1, figsize=figsize)
        self.interactive = interactive
        self.ticks = ticks
        if interactive:
            plt.ion()
        else:
            plt.ioff()
        if limits is not None:
            self.set_limits(*limits)
        if not ticks:
            self.no_ticks()
        plt.axis('equal')
        self._graphics = {}
        self._init_colors()

    def adjust_markers(self):
        figsize = plt.gcf().get_size_inches()
        r = min(figsize[0] / 8, figsize[1] / 6)
        mpl.rcParams['lines.markersize'] = 6 * r
        mpl.rcParams['lines.markeredgewidth'] = 0.5 * r
        mpl.rcParams['lines.linewidth'] = r
        mpl.rcParams['patch.linewidth'] = r

    def adjust_markersize(self, size):
        figsize = plt.gcf().get_size_inches()
        r = min(figsize[0] / 8, figsize[1] / 6)
        return 6 * r


    def axis_on(self, on):
        """Turn the axes and labels on or off."""
        if on:
            plt.axis('on')
        else:
            plt.axis('off')

    def clear(self):
        """Clear the plot area."""
        plt.cla()
        self._graphics = {}
        if not self.ticks:
            self.no_ticks()

    def close(self):
        """Close the plot."""
        self.clear()
        plt.close()

    def draw(self):
        """Draw a non-interactive plot."""
        plt.show()

    def hide(self, name):
        """Hide the layer with the given name."""
        try:
            graphics = self._graphics[name]
            graphic_type = type(graphics[0])
            if graphic_type is mpl.lines.Line2D:
                for graphic in graphics:
                    plt.axes().lines.remove(graphic)
            elif graphic_type is mpl.patches.Polygon or graphic_type is mpl.patches.PathPatch:
                for graphic in graphics:
                    plt.axes().patches.remove(graphic)
            else:
                raise RuntimeError('{} not supported'.format(graphic_type))
        except (KeyError, ValueError):
            pass

    def plot_line(self, data, symbol='', name='', **kwargs):
        """Plot a line.

        data   - list of (x, y) tuples
        symbol - optional pyplot symbol to draw the line with
        name   - optional name to assign to layer so can access it later
        kwargs - optional pyplot drawing parameters
        """
        graphics = self._plot_line(data, symbol, **kwargs)
        self._set_graphics(graphics, name, symbol or kwargs)

    def plot_multiline(self, data, symbol='', name='', **kwargs):
        """Plot a multiline.

        data   - list of lines, each of which is a list of (x, y) tuples
        symbol - optional pyplot symbol to draw the lines with
        name   - optional name to assign to layer so can access it later
        kwargs - optional pyplot drawing parameters
        """
        has_symbol = symbol or kwargs
        symbol = symbol or self._line_symbol()
        graphics = self._plot_multiline(data, symbol, **kwargs)
        self._set_graphics(graphics, name, has_symbol)

    def plot_multipoint(self, data, symbol='', name='', **kwargs):
        """Plot a multipoint.

        data   - list of (x, y) tuples
        symbol - optional pyplot symbol to draw the points with
        name   - optional name to assign to layer so can access it later
        kwargs - optional pyplot drawing parameters
        """
        has_symbol = symbol or kwargs
        symbol = symbol or self._point_symbol()
        graphics = self._plot_multipoint(data, **kwargs)
        self._set_graphics(graphics, name, has_symbol)

    def plot_multipolygon(self, data, color='', name='', **kwargs):
        """Plot a multipolygon.

        data   - list of polygons, each of which is a list of rings, each of
                 which is a list of (x, y) tuples
        color  - optional pyplot color to draw the polygons with
        name   - optional name to assign to layer so can access it later
        kwargs - optional pyplot drawing parameters
        """
        has_symbol = bool(color or kwargs)
        if not ('facecolor' in kwargs or 'fc' in kwargs):
            kwargs['fc'] = color or self._next_color()
        graphics = self._plot_multipolygon(data, **kwargs)
        self._set_graphics(graphics, name, has_symbol)

    def plot_point(self, data, symbol='', name='', **kwargs):
        """Plot a point.

        data   - (x, y) tuple
        symbol - optional pyplot symbol to draw the point with
        name   - optional name to assign to layer so can access it later
        kwargs - optional pyplot drawing parameters
        """
        has_symbol = symbol or kwargs
        symbol = symbol or self._point_symbol()
        graphics = self._plot_point(data, symbol, **kwargs)
        self._set_graphics(graphics, name, has_symbol)

    def plot_polygon(self, data, color='', name='', **kwargs):
        """Plot a polygon.

        data   - list of rings, each of which is a list of (x, y) tuples
        color  - optional pyplot color to draw the polygon with
        name   - optional name to assign to layer so can access it later
        kwargs - optional pyplot drawing parameters
        """
        has_symbol = bool(color or kwargs)
        if not ('facecolor' in kwargs or 'fc' in kwargs):
            kwargs['fc'] = color or self._next_color()
        graphics = self._plot_polygon(data, **kwargs)
        self._set_graphics(graphics, name, has_symbol)

    def remove(self, name):
        """Remove a layer with the given name."""
        try:
            self.hide(name)
            del self._graphics[name]
        except KeyError:
            pass

    def save(self, fn, dpi=300):
        plt.savefig(fn, dpi=dpi, bbox_inches='tight', pad_inches=0.02)

    def set_limits(self, x_min, x_max, y_min, y_max):
        """Set geographic limits for plotting."""
        self.x_lim = x_min, x_max
        self.y_lim = y_min, y_max
        self._set_limits()

    def show(self, name):
        """Show the layer with the given name."""
        try:
            graphics = self._graphics[name]
            graphic_type = type(graphics[0])
            if graphic_type is mpl.lines.Line2D:
                for graphic in graphics:
                    plt.axes().add_line(graphic)
            elif graphic_type is mpl.patches.Polygon or graphic_type is mpl.patches.PathPatch:
                for graphic in graphics:
                    plt.axes().add_patch(graphic)
            else:
                raise RuntimeError('{} not supported'.format(graphic_type))
        except KeyError:
            pass

    def no_ticks(self):
        plt.gca().get_xaxis().set_ticks([])
        plt.gca().get_yaxis().set_ticks([])

    def zoom(self, factor):
        """Zoom in or out by a percentage; negative is out."""
        x_min, x_max, y_min, y_max = plt.axis()
        x_delta = (x_max - x_min) * factor / 100
        y_delta = (y_max - y_min) * factor / 100
        plt.axis((x_min + x_delta, x_max - x_delta,
                  y_min + y_delta, y_max - y_delta))

    def _clockwise(self, data):
        """Determine if points are in clockwise order."""
        total = 0
        x1, y1 = data[0]
        for x, y in data[1:]:
            total += (x - x1) * (y + y1)
            x1, y1 = x, y
        x, y = data[0]
        total += (x - x1) * (y + y1)
        return total > 0

    def _codes(self, data):
        """Get a list of codes for creating a new PathPatch."""
        codes = np.ones(len(data), dtype=np.int) * Path.LINETO
        codes[0] = Path.MOVETO
        return codes

    def _init_colors(self):
        if mpl.__version__ >= '1.5':
            self.colors = list(mpl.rcParams['axes.prop_cycle'])
            self.current_color = -1
            self._next_color = self._next_color_new
        else:
            self._next_color = self._next_color_old

    def _line_symbol(self):
        """Get a default line symbol."""
        return self._next_color() + '-'

    def _next_color_old(self):
        """Get the next color in the rotation."""
        return next(plt.gca()._get_lines.color_cycle)

    def _next_color_new(self):
        """Get the next color in the rotation."""
        self.current_color += 1
        if self.current_color >= len(self.colors):
            self.current_color = 0
        return self.colors[self.current_color]['color']

    def _order_vertices(self, data, clockwise=True):
        """Order vertices in clockwise or counter-clockwise order."""
        self._clockwise(data) != clockwise or data.reverse()
        if data[0] != data[-1]:
            data.append(data[0])
        return data

    def _plot_line(self, data, symbol, **kwargs):
        x, y = zip(*data)
        return plt.plot(x, y, symbol, **kwargs)

    def _plot_multiline(self, data, symbol, **kwargs):
        """Plot a multiline."""
        graphics = []
        for line in data:
            graphics += self._plot_line(line, symbol, **kwargs)
        return graphics

    def _plot_multipoint(self, data, symbol, **kwargs):
        """Plot a multipoint."""
        graphics = []
        for point in data:
            graphics += self._plot_point(point, symbol, **kwargs)
        return graphics

    def _plot_multipolygon(self, data, **kwargs):
        """Plot a multipolygon."""
        graphics = []
        for poly in data:
            graphics += self._plot_polygon(poly, **kwargs)
        return graphics

    def _plot_point(self, data, symbol, **kwargs):
        """Plot a point."""
        return plt.plot(data[0], data[1], symbol, **kwargs)

    def _plot_polygon(self, data, **kwargs):
        """Plot a polygon."""
        outer = self._order_vertices(data[0], True)
        inner = [self._order_vertices(d, False) for d in data[1:]]
        vertices = np.concatenate(
            [np.asarray(outer)] + [np.asarray(i) for i in inner])
        codes = np.concatenate(
            [self._codes(outer)] + [self._codes(i) for i in inner])
        patch = PathPatch(Path(vertices, codes), **kwargs)
        plt.axes().add_patch(patch)
        return [patch]

    def _point_symbol(self):
        """Get a default point symbol."""
        return self._next_color() + 'o'

    def _same_type(self, graphic1, graphic2):
        """Determine if two graphics are of the same type."""
        if type(graphic1) is not type(graphic2):
            return False
        if type(graphic1) is mpl.patches.Polygon: ## huh?
            return True
        if len(graphic1.get_xdata()) == len(graphic2.get_xdata()):
            return True
        return len(graphic1.get_xdata()) > 1 and len(graphic2.get_xdata()) > 1

    def _set_graphics(self, graphics, name, has_symbol):
        """Add graphics to plot."""
        name = name or len(self._graphics)
        if name in self._graphics:
            self.hide(name)
            if not has_symbol and self._same_type(graphics[0], self._graphics[name][0]):
                styled_graphic = self._graphics[name][0]
                for graphic in graphics:
                    graphic.update_from(styled_graphic)
        self._graphics[name] = graphics
        plt.axis('equal')

    def _set_limits(self):
        """Set axis limits."""
        plt.xlim(*self.x_lim)
        plt.ylim(*self.y_lim)
        plt.axes().set_aspect('equal')


point_types = [ogr.wkbPoint, ogr.wkbPoint25D,
               ogr.wkbMultiPoint, ogr.wkbMultiPoint25D]
line_types = [ogr.wkbLineString, ogr.wkbLineString25D,
              ogr.wkbMultiLineString, ogr.wkbMultiLineString25D]
polygon_types = [ogr.wkbPolygon, ogr.wkbPolygon25D,
                 ogr.wkbMultiPolygon, ogr.wkbMultiPolygon25D]


def _get_layer(lyr_or_fn):
    """Get the datasource and layer from a filename."""
    if type(lyr_or_fn) is str:
        ds = ogr.Open(lyr_or_fn)
        if ds is None:
            raise OSError('Could not open {0}.'.format(lyr_or_fn))
        return ds.GetLayer(), ds
    else:
        return lyr_or_fn, None


class VectorPlotter(SimpleVectorPlotter):
    """Plots vector data represented as OGR layers and geometries."""

    def __init__(self, interactive, ticks=False, figsize=None, limits=None):
        """Construct a new VectorPlotter.

        interactive - boolean flag denoting interactive mode
        ticks       - boolean flag denoting whether to show axis tickmarks
        figsize     - optional figure size
        limits      - optional geographic limits (x_min, x_max, y_min, y_max)
        """
        super(VectorPlotter, self).__init__(interactive, ticks, figsize, limits)

    def plot(self, geom_or_lyr, symbol='', name='', **kwargs):
        """Plot a geometry or layer.
        geom_or_lyr - geometry, layer, or filename
        symbol      - optional pyplot symbol to draw the geometries with
        name        - optional name to assign to layer so can access it later
        kwargs      - optional pyplot drawing parameters
        """
        if type(geom_or_lyr) is str:
            lyr, ds = _get_layer(geom_or_lyr)
            self.plot_layer(lyr, symbol, name, **kwargs)
        elif type(geom_or_lyr) is ogr.Geometry:
            self.plot_geom(geom_or_lyr, symbol, name, **kwargs)
        elif type(geom_or_lyr) is ogr.Layer:
            self.plot_layer(geom_or_lyr, symbol, name, **kwargs)
        else:
            raise RuntimeError('{} is not supported.'.format(type(geom_or_lyr)))

    def plot_geom(self, geom, symbol='', name='', **kwargs):
        """Plot a geometry.
        geom   - geometry
        symbol - optional pyplot symbol to draw the geometry with
        name   - optional name to assign to layer so can access it later
        kwargs - optional pyplot drawing parameters
        """
        geom_type = geom.GetGeometryType()
        if not symbol:
            if geom_type in point_types:
                symbol = self._point_symbol()
            elif geom_type in line_types:
                symbol = self._line_symbol()
        if geom_type in polygon_types and not self._kwargs_has_color(**kwargs):
            kwargs['fc'] = symbol or self._next_color()
        graphics = self._plot_geom(geom, symbol, **kwargs)
        self._set_graphics(graphics, name, symbol or kwargs)

    def plot_layer(self, lyr, symbol='', name='', **kwargs):
        """Plot a layer.
        geom   - layer
        symbol - optional pyplot symbol to draw the geometries with
        name   - optional name to assign to layer so can access it later
        kwargs - optional pyplot drawing parameters
        """
        geom_type = lyr.GetLayerDefn().GetGeomType()
        if geom_type == ogr.wkbUnknown:
            feat = lyr.GetFeature(0)
            geom_type = feat.geometry().GetGeometryType()
        if not symbol:
            if geom_type in point_types:
                symbol = self._point_symbol()
            elif geom_type in line_types:
                symbol = self._line_symbol()
        if geom_type in polygon_types and not self._kwargs_has_color(**kwargs):
            kwargs['fc'] = symbol or self._next_color()
        lyr.ResetReading()
        graphics = []
        for feat in lyr:
            graphics += self._plot_geom(feat.geometry(), symbol, **kwargs)
        self._set_graphics(graphics, name, symbol or kwargs)
        lyr.ResetReading()

    def _plot_geom(self, geom, symbol='', **kwargs):
        """Plot a geometry."""
        geom_name = geom.GetGeometryName()
        if geom_name == 'POINT':
            symbol = symbol or self._point_symbol()
            return self._plot_point(self._get_point_coords(geom), symbol, **kwargs)
        elif geom_name == 'MULTIPOINT':
            symbol = symbol or self._point_symbol()
            return self._plot_multipoint(self._get_multipoint_coords(geom), symbol, **kwargs)
        elif geom_name == 'LINESTRING':
            return self._plot_line(self._get_line_coords(geom), symbol, **kwargs)
        elif geom_name == 'MULTILINESTRING':
            return self._plot_multiline(self._get_multiline_coords(geom), symbol, **kwargs)
        elif geom_name == 'POLYGON':
            return self._plot_polygon(self._get_polygon_coords(geom), **kwargs)
        elif geom_name == 'MULTIPOLYGON':
            return self._plot_multipolygon(self._get_multipolygon_coords(geom), **kwargs)
        elif geom_name == 'GEOMETRYCOLLECTION':
            graphics = []
            for i in range(geom.GetGeometryCount()):
                graphics += self._plot_geom(geom.GetGeometryRef(i), symbol, **kwargs)
            return graphics
        else:
            raise RuntimeError('{} not supported'.format(geom_name))

    def _get_line_coords(self, geom):
        """Get line coordinates as a list of (x, y) tuples."""
        return [coords[:2] for coords in geom.GetPoints()]

    def _get_point_coords(self, geom):
        """Get point coordinates as an (x, y) tuple."""
        return (geom.GetX(), geom.GetY())

    def _get_polygon_coords(self, geom):
        """Get polygon coordinates as a list of lists of (x, y) tuples."""
        coords = []
        for i in range(geom.GetGeometryCount()):
            coords.append(self._get_line_coords(geom.GetGeometryRef(i)))
        return coords

    def _get_multiline_coords(self, geom):
        """Get multiline coordinates as a list of lists of (x, y) tuples."""
        coords = []
        for i in range(geom.GetGeometryCount()):
            coords.append(self._get_line_coords(geom.GetGeometryRef(i)))
        return coords

    def _get_multipoint_coords(self, geom):
        """Get multipoint coordinates as a list of (x, y) tuples."""
        coords = []
        for i in range(geom.GetGeometryCount()):
            coords.append(self._get_point_coords(geom.GetGeometryRef(i)))
        return coords

    def _get_multipolygon_coords(self, geom):
        """Get multipolygon coordinates as a list of lists rings."""
        coords = []
        for i in range(geom.GetGeometryCount()):
            coords.append(self._get_polygon_coords(geom.GetGeometryRef(i)))
        return coords

    def _kwargs_has_color(self, **kwargs):
        """Check if kwargs dictionary has a facecolor entry."""
        return 'fc' in kwargs or 'facecolor' in kwargs


if __name__=='__main__':
    vp = VectorPlotter(False)
    vp.plot('data/global/ne_50m_admin_0_countries.shp', fill=False)
    vp.plot('data/global/ne_50m_populated_places.shp', 'bo')
    vp.draw()
