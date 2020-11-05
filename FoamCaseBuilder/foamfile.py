# coding=utf-8

from __future__ import print_function, absolute_import

"""Foam File Class."""

import os
import os.path
import json
import collections
from copy import deepcopy

# used in header() function only, can be replaced by FoamCaseBuilder's
#from .version import Version, Header

from .config import getFoamVersion
from .FoamTemplateString import getFoamFileHeader

# used in class FoamFileZeroFolder(FoamFile), this will be removed in this adaption
#from .utilities import get_boundary_field_from_geometries

from .parser import CppDictParser

#from collections.abc import MutableMapping
#in python2  it is in module collections, a lot of API to change,
#derived from MutableMapping, can make it as dict type
class ParsedParameterFile(object):
    """ adapter class to simulate PyFoam API """
    def __init__(self, fpath, *args, **kw):
        """
        Initialize a case from a file.

        Args:
            self: (todo): write your description
            fpath: (str): write your description
            kw: (todo): write your description
        """
        #parse filepath to case, location, name
        location_path, name = os.path.split(fpath)
        cls = 'dictionary'
        self.case_path, location = os.path.split(location_path)
        if location[0] == '0':
            self.foamFile = FoamFileZeroFolder(name, cls, location)
        else:
            self.foamFile = FoamFile(name, cls, location)
        self.foamFile.from_file(fpath)
        self.content = self.foamFile.values

    def items(self):
        """
        Returns the items.

        Args:
            self: (todo): write your description
        """
        return self.content.items()
    def keys(self):
        """
        Return a list of all keys.

        Args:
            self: (todo): write your description
        """
        return self.content.keys()
    def values(self):
        """
        Return the values.

        Args:
            self: (todo): write your description
        """
        return self.content.values()

    # dict-like API
    def __contains__(self,key):
        """
        Determine if the given key is contained content.

        Args:
            self: (todo): write your description
            key: (todo): write your description
        """
        return key in self.content

    def __getitem__(self,key):
        """
        Return the value of a key.

        Args:
            self: (todo): write your description
            key: (str): write your description
        """
        return self.content[key]

    def __setitem__(self,key,value):
        """
        Sets the value of a key.

        Args:
            self: (todo): write your description
            key: (str): write your description
            value: (str): write your description
        """
        self.content[key]=value

    def __delitem__(self,key):
        """
        Removes an item from the cache.

        Args:
            self: (todo): write your description
            key: (str): write your description
        """
        del self.content[key]

    def __len__(self):
        """
        Returns the length of the content.

        Args:
            self: (todo): write your description
        """
        return len(self.content)

    def __iter__(self):
        """
        Iterate over the content.

        Args:
            self: (todo): write your description
        """
        for key in self.content:
            yield key
    # the only API used in FoamCaseBuilder
    def writeFile(self):
        """
        Writes the case to disk.

        Args:
            self: (todo): write your description
        """
        # def save(self, project_folder, sub_folder=None, overwrite=True)
        self.foamFile.save(self.case_path)

class BoundaryDict(ParsedParameterFile):
    """ adapter class to simulate PyFoam API """
    def __init__(self, case_path, *args, **kw):
        """
        Initialize case data.

        Args:
            self: (todo): write your description
            case_path: (str): write your description
            kw: (todo): write your description
        """
        #build filepath from case, location, name
        cls = 'dictionary'
        location = "constant/polyMesh"
        name = 'boundary'
        self.case_path = case_path
        fpath = os.path.join(self.case_path, location, name)
        self.foamFile = FoamFile(name, cls, location)
        print('try to load boundary dict')
        self.foamFile.from_file(fpath)
        self.content = self.foamFile.values
        print(self.foamFile.values)

    def patches(self):
        """
        Returns a list of all keys.

        Args:
            self: (todo): write your description
        """
        return self.foamFile.keys()

class FoamFile(object):
    """FoamFile base class for OpenFOAM dictionaries.

    Read (http://cfd.direct/openfoam/user-guide/basic-file-format/) for
    more information about FoamFile

    Attributes:
        name: Filename (e.g. controlDict)
        cls: OpenFOAM class constructed from the data file
            concerned. Typically  dictionary  or a field, e.g. volVectorField
        location: Folder name (0, constant or system)
        file_format: File format (ascii / binary) (default: ascii)
    """

    __locations = ('0', 'system', 'constant', 'constant/polyMesh', '0.orig')

    def __init__(self, name, cls, location=None, file_format="ascii",
                 default_values=None, values=None):
        """Init foam file."""
        self.__dict__['is{}'.format(self.__class__.__name__)] = True
        self.__version = "{}.{}".format(getFoamVersion()[0], getFoamVersion()[1])
        self.format = str(file_format)  # ascii / binary
        self.cls = str(cls)  # dictionary or field
        self.name = str(name)
        self.location = location  # location is optional
        if self.location:
            if self.location.replace('"', '') in self.__locations:
                self.location = '"' + self.location.replace('"', '') + '"'
            else:
                raise ValueError(
                    '{} is not a valid OpenFOAM location: {}'.format(
                        self.location, self.__locations
                    )
                )

        # Initiate values
        if not values:
            values = {}
        if not default_values:
            default_values = {}
        self.__values = deepcopy(default_values)
        self.update_values(values, mute=True)

    @classmethod
    def from_file(cls, filepath, location=None):
        """Create a FoamFile from a file.

        Args:
            filepath: Full file path to dictionary.
            location: Optional folder name for location (0, constant or system)
        """
        def _try_get_foam_file_value(key):
            """Get values for FoamFile header."""
            try:
                return _values['FoamFile'][key]
            except KeyError:
                msg = 'failed to find ""{}"" in {} header.\nDefault value: {}' \
                    .format(key, filepath, default[key])
                print(msg)
                return default[key]

        assert not filepath.endswith('blockMeshDict'), \
            'To parse blockMeshDict from file use BlockMeshDict.from_file()'

        _values = CppDictParser.from_file(filepath).values
        p, _name = os.path.split(filepath)

        default = {
            'object': _name,
            'class': 'dictionary',
            'location': None,
            'format': 'ascii'
        }

        # set up FoamFile dictionary
        _name = _try_get_foam_file_value('object')
        _cls = _try_get_foam_file_value('class')
        _location = _try_get_foam_file_value('location')
        _file_format = _try_get_foam_file_value('format')

        if 'FoamFile' in _values:
            del(_values['FoamFile'])

        return cls(_name, _cls, _location, _file_format, values=_values)

    @property
    def isFoamFile(self):
        """Return True for FoamFile."""
        return True

    @property
    def is_zero_file(self):
        """Check if the file location is folder 0."""
        if not self.location:
            return False
        return self.location == "0"

    @property
    def is_constant_file(self):
        """Check if the file location is 'constant' folder."""
        if not self.location:
            return False
        return self.location == "constant"

    @property
    def is_system_file(self):
        """Check if the file location is 'system' folder."""
        if not self.location:
            return False
        return self.location == "system"

    @property
    def values(self):
        """Return values as a dictionary."""
        return self.__values

    # TODO(Mostapha): replace log changes with update_dict from utilities
    def update_values(self, v, replace=False, mute=False):
        """Update current values from dictionary v.

        if key is not available in current values it will be added, if the key
        already exists it will be updated.

        Returns:
            True is the dictionary is updated.
        """
        def log_changes(original, new):
            """compare this dictionary with the current values."""
            if original is None:
                original = {}

            for key, value in new.items():

                if key not in original:
                    # there is a new key so dictionary has changed.
                    if not mute:
                        msg = '{} :: New values are added for {}.' \
                            .format('.'.join(self.__parents), key)
                        print(msg)
                    self.__hasChanged = True
                    return

                if isinstance(value, (dict, collections.OrderedDict)):
                    self.__parents.append(key)
                    log_changes(original[key], value)
                elif str(original[key]) != str(value):
                    # there is a change in value
                    if not mute:
                        msg = '{}.{} is changed from "{}" to "{}".'\
                            .format('.'.join(self.__parents), key,
                                    original[key] if len(str(original[key])) < 100
                                    else '%s...' % str(original[key])[:100],
                                    value if len(str(value)) < 100
                                    else '%s...' % str(value)[:100])
                        print(msg)
                    self.__hasChanged = True
                    return

        def modify_dict(original, new):
            """Modify a dictionary based on a new dictionary."""
            for key, value in new.items():
                if key in original and isinstance(value, dict):
                    if isinstance(original[key], dict):
                        modify_dict(original[key], value)
                    else:
                        # the value was not a dict, replce them with the new one
                        original[key] = value
                else:
                    original[key] = value

            return original

        assert isinstance(v, dict), 'Expected dictionary not {}!'.format(type(v))

        self.__parents = [self.__class__.__name__]
        self.__hasChanged = False
        log_changes(self.__values, v)

        if self.__hasChanged:
            if replace:
                self.__values.update(v)
            else:
                self.__values = modify_dict(self.__values, v)
            return True
        else:
            return False

    @property
    def parameters(self):
        """Get list of parameters."""
        return self.values.keys()

    def get_value_by_parameter(self, parameter):
        """Get values for a given parameter by parameter name.

        Args:
            parameter: Name of a parameter as a string.
        """
        try:
            return self.values[parameter]
        except KeyError:
            raise KeyError('{} is not available in {}.'.format(
                parameter, self.__class__.__name__
            ))

    def set_value_by_parameter(self, parameter, value):
        """Set value for a parameter.

        Args:
            parameter: Name of a parameter as a string.
            value: Parameter value as a string.
        """
        self.values[parameter] = value

    def header(self):
        """Return open foam style string."""
        return getFoamFileHeader(self.location, self.name, self.cls)
        """
        if self.location:
            return Header.header() + \
                "FoamFile\n{\n" \
                "\tversion\t\t%s;\n" \
                "\tformat\t\t%s;\n" \
                "\tclass\t\t%s;\n" \
                "\tlocation\t%s;\n" \
                "\tobject\t\t%s;\n" \
                "}\n" % (self.__version, self.format, self.cls, self.location,
                         self.name)
        else:
            return Header.header() + \
                "FoamFile\n{\n" \
                "\tversion\t\t%s;\n" \
                "\tformat\t\t%s;\n" \
                "\tclass\t\t%s;\n" \
                "\tobject\t\t%s;\n" \
                "}\n" % (self.__version, self.format, self.cls, self.name)
        """

    @staticmethod
    def _split_line(line):
        """Split lines which ends with { to two lines."""
        return line[4:-1] + "\n" + \
            (len(line) - len(line.strip()) - 4) * ' ' + '{'

    def body(self):
        """Return body string."""
        # remove None values
        def remove_none(d):
            """
            Recursively remove empty dict.

            Args:
                d: (dict): write your description
            """
            if isinstance(d, (dict, collections.OrderedDict)):
                return collections.OrderedDict(
                    (k, remove_none(v)) for k, v in d.iteritems()
                    if v == {} or (v and remove_none(v)))
            elif isinstance(d, (list, tuple)):
                return [remove_none(v) for v in d if v and remove_none(v)]
            else:
                return d
            return remove_none

        _values = remove_none(self.values)

        # make python dictionary look like c++ dictionary!!
        of = json.dumps(_values, indent=4, separators=(";", "\t\t")) \
            .replace('\\"', '@').replace('"\n', ";\n").replace('"', '') \
            .replace('};', '}').replace('\t\t{', '{').replace('@', '"')

        # remove first and last {} and prettify[!] the file
        content = (line[4:] if not line.endswith('{') else self._split_line(line)
                   for line in of.split("\n")[1:-1])

        return "\n\n".join(content)

    @staticmethod
    def convert_bool_value(v=True):
        """Convert Boolean values to on/off string."""
        _v = ('off', 'on')

        if v in _v:
            return v

        if v:
            return 'on'
        else:
            return 'off'

    def to_openfoam(self):
        """Return OpenFOAM string."""
        return "\n".join((self.header(), self.body()))

    def save(self, project_folder, sub_folder=None, overwrite=True):
        """Save to file.

        Args:
            project_folder: Path to project folder as a string.
            sub_folder: Optional input for sub_folder (default: self.location).
        """
        sub_folder = sub_folder or self.location.replace('"', '')
        fp = os.path.join(project_folder, sub_folder, self.name)

        if not overwrite and os.path.isfile(fp):
            return

        with open(fp, "wb") as outf:
            outf.write(self.to_openfoam())
        return fp

    def __eq__(self, other):
        """Check equality."""
        return self.values == other.values

    def duplicate(self):
        """Return a copy of this object."""
        return deepcopy(self)

    def ToString(self):
        """Overwrite .NET ToString method."""
        return self.__repr__()

    def __repr__(self):
        """Class representation."""
        return self.to_openfoam()

class FoamFileZeroFolder(FoamFile):
    """FoamFiles under 0 folder.
    The main difference between FoamFileZeroFolder and FoamFile is that
    FoamFileZeroFolder has a method to set boundary fields based on input
    geometry (e.g. Butterfly objects).
    """

    @classmethod
    def from_bf_geometries(cls, bf_geometries, values=None):
        """Init class by bf_geometries."""
        _cls = cls(values)
        _cls.set_boundary_field(bf_geometries)
        return _cls

    def set_boundary_field(self, bf_geometries):
        """Set FoamFile boundaryField values from bf_geometries.
        Args:
            bf_geometries: List of Butterfly geometries.
        """
        self.values['boundaryField'] = \
            get_boundary_field_from_geometries(bf_geometries, self.name)

    def get_boundary_field(self, name):
        """Try to get boundaryField value for a geometry by name.
        Args:
            name: Geometry name.
        Returns:
            An OpenFOAM field if name is in boundaryFields.
        """
        if name in self.values['boundaryField']:
            return self.values['boundaryField'][name]
        else:
            print('Failed to find boundaryField values for {}'.format(name))

class Condition(FoamFile):
    """OpenFOAM conditions object.

    Use this class to create conditions such as initialConditions and ABLConditions.
    Conditions don't have OpenFOAM header. It's only values.
    """

    def header(self):
        """Return conditions header."""
        return "/* OpenFOAM conditions object */"


def foam_file_from_file(filepath, name=None, header=False):
    """Load values from foamfile.

    Args:
        filepath: Full file path to dictionary.
        name: An optional name for foamfile to double check.
        header: Set to True to get FoamFile data.
    """
    if name:
        p, _name = os.path.split(filepath)
        assert _name.lower() == name.lower(), \
            'Illegal file input {} for creating {}'.format(_name, name)

    _values = CppDictParser.from_file(filepath).values

    if not header and 'FoamFile' in _values:
        del(_values['FoamFile'])

    return _values
