#! /usr/bin/env python

# coordinate system classes, conversion between coordinate systems

from tf import transformations
import numpy
from math import radians
from itertools import repeat


class Position(object):
    def __init__(self, owner_cs, x=0, y=0, z=0):
        """
        :rtype : Position
        """
        self.owner = owner_cs
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        # return a string with formatted x,y and z coordinates
        return str(self.owner) + " " + "{:7.4f}".format(self.x) + "|" + "{:7.4f}".format(self.y) + "|" + "{:7.4f}".format(self.z)

    @property
    def clone(self):
        # return independent copy of this Position
        return Position(self.owner, self.x, self.y, self.z)

    @property
    def tuple(self):
        # return coordinates as tuple
        return self.x, self.y, self.z

    @tuple.setter
    def tuple(self, (x, y, z)):
        # set coordinates as tuple
        self.x = x
        self.y = y
        self.z = z

    def distance_to(self, position):
        # return distance from this position to position passed as argument

        # make sure both positions are in the same coordinate system
        conv_pos = self.owner.to_this(position)

        return ((self.x - conv_pos.x) ** 2 + (self.y - conv_pos.y) ** 2 + (self.z - conv_pos.z) ** 2) ** 0.5

    @property
    def distance_to_origin(self):
        # return distance from this position to the origin of parent coordinate system
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5


class CoordinateSystem(object):
    def __init__(self, parent_cs, name, x, y, z, rotx, roty, rotz):
        """
        :rtype : CoordinateSystem
        :type parent_cs: CoordinateSystem
        """
        self.parent = parent_cs
        self.name = name

        self._x = x
        self._y = y
        self._z = z
        self._rotx = rotx
        self._roty = roty
        self._rotz = rotz

        self._mat_from_parent = None
        self._mat_to_parent = None

        # these values are used to backup and restore pose of coordinate system
        self._x_stored = x
        self._y_stored = y
        self._z_stored = z
        self._rotx_stored = rotx
        self._roty_stored = roty
        self._rotz_stored = rotz

        self.redefine(x, y, z, rotx, roty, rotz)

    @property
    def __str__(self):
        return self.name

    @property
    def origin(self):
        # returns position with 0,0,0 coordinates in this coordinate system
        return Position(self)

    @property
    def translation(self):
        # return linear component of coordinate system definition as tuple
        return self._x, self._y, self._z

    @property
    def rotation_zxy_rad(self):
        # return angular component of coordinate system definition as tuple in ZXY order
        return radians(self.rotz), radians(self._rotx), radians(self._roty)

    @property
    def rotx(self):
        return self._rotx

    @property
    def roty(self):
        return self._roty

    @property
    def rotz(self):
        return self._rotz

    @property
    def mat_to_parent(self):
        return self._mat_to_parent

    @property
    def mat_from_parent(self):
        return self._mat_from_parent

    def redefine_tuple(self, (x, y, z)=(None, None, None), (rotx, roty, rotz)=(None, None, None)):
        # redefine pose of this coordinate system with a tuple of parameters
        self.redefine(x, y, z, rotx, roty, rotz)

    def redefine(self, new_x=None, new_y=None, new_z=None, new_rotx=None, new_roty=None, new_rotz=None):
        # redefine pose of this coordinate system with a set of individual parameters

        if new_x is None:
            x = self._x
        else:
            x = new_x
            self._x = new_x

        if new_y is None:
            y = self._y
        else:
            y = new_y
            self._y = new_y

        if new_z is None:
            z = self._z
        else:
            z = new_z
            self._z = new_z

        if new_rotx is None:
            rotx = self._rotx
        else:
            rotx = new_rotx
            self._rotx = new_rotx

        if new_roty is None:
            roty = self._roty
        else:
            roty = new_roty
            self._roty = new_roty

        if new_rotz is None:
            rotz = self.rotz
        else:
            rotz = new_rotz
            self._rotz = new_rotz

        self._mat_to_parent = calc_transformation_matrix(x, y, z, rotx, roty, rotz)
        self._mat_from_parent = None  # to save time, this matrix is only filled when necessary

    def update_mat_from_parent(self):
        # update matrix for conversion from parent coordinate system to this coordinate system
        self._mat_from_parent = numpy.linalg.inv(self._mat_to_parent)

    def get_derivative(self, name, d_x=None, d_y=None, d_z=None, d_rotx=None, d_roty=None, d_rotz=None):
        # return a new coordinate system (sharing the same parent) offset and/or rotated with this coordinate system used as reference

        if d_x is None:
            x = self._x
        else:
            x = self._x + d_x

        if d_y is None:
            y = self._y
        else:
            y = self._y + d_y

        if d_z is None:
            z = self._z
        else:
            z = self._z + d_z

        if d_z is None:
            rotx = self._rotx
        else:
            rotx = self._rotx + d_rotx

        if d_z is None:
            roty = self._roty
        else:
            roty = self._roty + d_roty

        if d_z is None:
            rotz = self.rotz
        else:
            rotz = self.rotz + d_rotz

        return CoordinateSystem(self.parent, name, x, y, z, rotx, roty, rotz)

    def backup(self):
        # stores definition of coordinate system to enable future rollback
        self._x_stored = self._x
        self._y_stored = self._y
        self._z_stored = self._z
        self._rotx_stored = self._rotx
        self._roty_stored = self._roty
        self._rotz_stored = self._rotz

    def rollback(self):
        # rolls back the coordinate system definition to the stored values
        self.redefine(self._x_stored, self._y_stored, self._z_stored, self._rotx_stored, self._roty_stored, self._rotz_stored)

    @property
    def to_root(self):
        # returns list of coordinate systems (nodes) between this coordinate system and its topmost ancestor (root)

        root_list = list()
        root_list.append(self)

        current = self
        while current.parent is not None:
            root_list.append(current.parent)
            current = current.parent

        return root_list

    def to_this(self, position):
        # converts position passed as argument to this coordinate system

        """
        :rtype : Position
        """

        # if position is already in this coordinate system -- just return it
        if position.owner is self:
            return position

        position_in_this = Position(self)

        def fill_position(arr):
            # fills position coordinates with values from array
            position_in_this.x = arr[0][0]
            position_in_this.y = arr[1][0]
            position_in_this.z = arr[2][0]

        # transform position to array
        pos_array = numpy.array([[position.x], [position.y], [position.z], [1]])

        # does position belong to immediate relative of this cs?
        if position.owner.parent is self:
            # yes, position belongs to child of this cs
            new_pos_array = numpy.dot(position.owner.mat_to_parent, pos_array)
            fill_position(new_pos_array)

        elif position.owner is self.parent:
            # yes, position belongs to parent of this cs
            if self._mat_from_parent is None:
                # make sure matrix for transformation to parent is filled
                self.update_mat_from_parent()
            new_pos_array = numpy.dot(self.mat_from_parent, pos_array)
            fill_position(new_pos_array)

        else:
            # no, its not an immediate relative

            # let's get transformation matrices for full conversion route
            transformation_matrices = list()
            conversion_route = route(position.owner, self)
            if conversion_route is None:
                raise Exception("Could not convert " + str(position) + " to " + str(self) + ": conversion route could not be found.")
            else:
                for node in conversion_route:
                    if node[1] == "up":
                        # going up, so to_parent matrix of this node is needed
                        transformation_matrices.append(node[0].mat_to_parent)

                    elif node[1] == "down":
                        # going down, so from_parent matrix of this node is needed
                        if node[0].mat_from_parent is None:
                            node[0].update_mat_from_parent()
                        transformation_matrices.append(node[0].mat_from_parent)
                    else:
                        # means we have "root" node here, no matrices are needed from it
                        pass

                aggregate_transformation = reduce(numpy.dot, transformation_matrices[::-1])
                new_pos_array = numpy.dot(aggregate_transformation, pos_array)
                fill_position(new_pos_array)
                # old_pos = self.to_this_old(position, caller, recursive)
                # return old_pos

        return position_in_this


def closest_common_node(cs1, cs2):
    # returns the lowest node in the tree of coordinate system relationships, which appears in both routes from cs1 to root and from cs2 to root

    """
    :type cs1: CoordinateSystem
    :type cs2: CoordinateSystem
    """
    cs1_to_root = cs1.to_root
    cs2_to_root = cs2.to_root

    for node in cs1_to_root:
        if node in cs2_to_root:
            return node


route_base = dict()  # already found conversion routes; this allows to avoid multiple constructions of the same route


def route(from_cs, to_cs):
    # returns list of coordinate systems, successive conversion between which results in conversion from "from_cs" to "to_cs"

    """
    :rtype : list
    :type from_cs: CoordinateSystem
    :type to_cs: CoordinateSystem
    """

    route_desc = from_cs.name + "-" + to_cs.name
    if route_desc in route_base:
        return route_base[route_desc]

    cs1_to_root = from_cs.to_root
    cs2_to_root = to_cs.to_root

    built_route = list()

    for node in cs1_to_root:
        built_route.append((node, "up"))
        if node in cs2_to_root:
            built_route[-1] = (node, "root")
            intersection_index = cs2_to_root.index(node)
            if intersection_index > 0:
                built_route.extend(zip(cs2_to_root[intersection_index - 1::-1], repeat("down")))
            route_base[route_desc] = built_route

            return built_route

    return None


def calc_transformation_matrix(x, y, z, rotx, roty, rotz):
    # return transformation matrix based on translation and rotation components
    r_mat = transformations.euler_matrix(radians(rotz), radians(rotx), radians(roty), 'rzxy')
    t_mat = transformations.translation_matrix((x, y, z))

    return numpy.dot(t_mat, r_mat)
