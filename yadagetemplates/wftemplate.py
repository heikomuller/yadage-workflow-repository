"""Workflow template loader - Workflow templates contain a unique identifier,
a name, and description. The main component of the template is the workflow
schema. In addition, some workfows may have a list of initial user provided
parameters that are needed to run the workflow.

Workflow schema may be stored in various formats. The source handle is a
description of the schema format. By now, three different types of source are
supported: CAP, JSON files, and YAML files. For the latter, the schema may be
stored accross multiple files that are referenced from within other files.
"""
from abc import abstractmethod
import json
from jsonschema import Draft4Validator, validators
import logging
import urllib2
import urlparse
import yaml


# ------------------------------------------------------------------------------
#
# Constants
#
# ------------------------------------------------------------------------------

"""Valid source types."""
TYPE_CAP = 'CAP'
TYPE_JSON = 'JSON'
TYPE_YAML = 'YAML'

TYPES = [TYPE_CAP, TYPE_JSON, TYPE_YAML]


# ------------------------------------------------------------------------------
#
# Workflow Templates
#
# ------------------------------------------------------------------------------

class WorkflowTemplate(object):
    """The template class combines the attributes of a workflow template.

    Attributes
    ----------
    identifier : string
        Unique template identifier
    name : string
        Descriptive template name
    description : string
        Extended description about workflow
    schema : JSON
        Workflow schema source definition {'type', ..., 'properties':{}}
    parameters : JSON, optional
        Initialization parameters when executing the represented workflow
    """
    def __init__(self, identifier, name, description, schema, parameters=None):
        """Initialize the  workflow template instance.

        Parameters
        ----------
        identifier : string
            Unique template identifier
        name : string
            Descriptive template name
        description : string
            Extended description about workflow
        schema : JSON
            Workflow schema source definition {'type', ..., 'properties':{}}
        parameters : JSON, optional
            Initialization parameters when executing the represented workflow
        """
        self.identifier = identifier
        self.name = name
        self.description = description
        self.schema = schema
        self.parameters = parameters

    @staticmethod
    def from_json(json_obj):
        """Create workflow template instance from a Json object. Expects
        elements for each template attribute that correspond in name to the
        attribute name.

        Parameters
        ----------
        json_obj : JSON
            Json object containing the template information
        """
        # Get schema source handle and the read the schema information
        schema = SourceHandle.from_json(json_obj['schema']).read()
        # The parameters defintion is optional
        if 'parameters' in json_obj:
            parameters =json_obj['parameters']
        else:
            parameters = None
        # Create and return instance of workflow template class
        return WorkflowTemplate(
            json_obj['identifier'],
            json_obj['name'],
            json_obj['description'],
            schema,
            parameters=parameters
        )


class WorkflowTemplateRepository(object):
    """Repository of workflow templates. Each template has a unique identifier,
    name, description, and schema. The schema is validated against the general
    YADAGE workflow schema definition (captured in the repositories validator).
    """
    def __init__(self, schema):
        """Initialize an empty repository and the workflow schema validator.
        The schema defintion is read from the given schema source handle. The
        validation code has been copied from cap-schemas.

        Parameters
        ----------
        schema : JSON
            Json object containing YADAGE workflow schema definition.
        """
        self.db = {}
        DefaultValidatingDraft4Validator = extend_with_default(Draft4Validator)
        self.validator = DefaultValidatingDraft4Validator(schema)

    def get(self, key):
        """Get workflow template with given identifier.

        Parameters
        ----------
        key : string
            Unique workflow identifier

        Returns
        -------
        WorkflowTemplate
            Workflow template associated with the given key.
        """
        if key in self.db:
            return self.db[key]
        else:
            return None

    def list(self):
        """List of all workflow tempates in templates in the repository. List
        items are sorted by their name.

        Returns
        -------
        list
            List of workflow templates
        """
        return sorted(self.db.values(), key=lambda wf: wf.name)

    def load(self, listing):
        for item in listing:
            # Make the load process fail save. Will log error messages for
            # templates that fail to load but will not fail the load process.
            try:
                wf = WorkflowTemplate.from_json(item)
                if wf.identifier in self.db:
                    raise ValueError('duplicate workflow template: ' + wf.identifier)
                self.validator.validate(wf.schema)
                self.db[wf.identifier] = wf
            except Exception as ex:
                logging.error(ex)

# ------------------------------------------------------------------------------
#
# Sources
#
# ------------------------------------------------------------------------------

class SourceHandle(object):
    """Source handle contains information about a workflow template schema that
    is loadable either from a file on local disk or an Web resource. Provides
    read() method to get a Json representation of the references workflow
    template schema.
    """
    def __init__(self, type, properties):
        """Initialize the source type and type specific properties.

        Raises a ValueError if the source type is unknown.

        Parameters
        ----------
        type : string
            Source type identifier
        properties : dict()
            Source specific properties
        """
        # Ensure that the source type is in the list of supported types
        if not type in TYPES:
            raise ValueError('invalid source type: ' + type)
        self.type = type
        self.properties = properties

    @staticmethod
    def from_json(obj):
        """Create source handle instance form Json object. Expects an object
        with two elements: type is a string and properties is a dictionary.

        Parameters
        ----------
        obj : JSON
            Json object containing the source handle definition

        Returns
        -------
        SourceHandle
        """
        return SourceHandle(obj['type'], obj['properties'])

    def read(self):
        """ Reads the template schema from the given source.

        For a CAP source properties 'baseUri' and 'resourceId' are expected,
        that reference the CAP server and the workflow identifier, respectively.

        For JSON and YAML resource the 'resourceUri' is expected as source
        property. In addition, a property 'baseUri' may be given that is used to
        evaluate references against.

        Returns
        -------
        JSON
            Json representation of the the workflow template schema
        """
        if self.type == TYPE_CAP:
            # Expects a 'baseUri' and 'resourceId' element as properties
            for key in ['baseUri', 'resourceId']:
                if not key in self.properties:
                    raise ValueError('missing property: ' + key + ' in ' + str(self.properties))
            # Read the whole workflow repository.
            data = ResourceReader().read(self.properties['baseUri'])
            schema = None
            resource_id = self.properties['resourceId']
            # Extract workflow with given identifier
            for wf in data['metadata']['_metadata']['workflows']:
                if wf['name'] == resource_id:
                    schema = wf['workflow']
                    break
            # Raise exception if workflow with given id does not exist
            if schema is None:
                raise ValueError('unknown workflow: ' + resource_id)
        elif self.type == TYPE_JSON:
            # Expects 'resourceUri' as property.
            if not 'resourceUri' in self.properties:
                raise ValueError('missing property: resourceUri in ' + str(self.properties))
            resource_uri = self.properties['resourceUri']
            # Base Uri to evaluate references against is optional
            if 'baseUri' in self.properties:
                base_uri = self.properties['baseUri']
            else:
                base_uri = None
            schema = JSONLoader(base_uri=base_uri).load(resource_uri)
        elif self.type == TYPE_YAML:
            # Expects 'resourceUri' as property.
            if not 'resourceUri' in self.properties:
                raise ValueError('missing property: resourceUri in ' + str(self.properties))
            resource_uri = self.properties['resourceUri']
            # Base Uri to evaluate references against is optional
            if 'baseUri' in self.properties:
                base_uri = self.properties['baseUri']
            else:
                base_uri = None
            schema = YAMLLoader(base_uri=base_uri).load(resource_uri)
        else:
            raise ValueError('invalid source type: ' + self.type)
        return schema


# ------------------------------------------------------------------------------
#
# Resource Reader
#
# ------------------------------------------------------------------------------

class ObjectLoader(object):
    """De-referencing reader for Json objects. Resolves references in the read
    documents.

    The loader maintains an internal cache to avoid loading the same referenced
    resource multiple times.

    Attributes
    ----------
    base_uri : string
        Base Uri against which references are resolved
    """
    def __init__(self, base_uri=None):
        """Initialize the base Uri used to resolve references and the resource
        cache.

        Parameters
        ----------
        base_uri : string, optional
            Unique resource identifier
        """
        self.base_uri = base_uri
        # Resource cache is a dictionary of read resources.
        self.cache = {}

    def load(self, uri):
        """Load Json document (or document fragment) at given Uri. The format of
        the document has to match the format that the implementation of the
        abstract read method expects.

        Only if the resource is not in the local cache it will be read from disk
        or from  the Web. All references in the read object will be resolved.
        Currently, references are expected to be dictionaries that contain a
        single element '$ref'.

        If the Uri contains a fragment only the part of the document that
        matches the fragment (after resolving references) will be returned.

        Parameters
        ----------
        uri : string
            Unique identifier of the resource

        Returns
        -------
        JSON
            Json representation of the resource
        """
        # Get Uri fragment if exists. Variable resource_uri will contain the
        # base Uri of the resource
        pos = uri.find('#')
        if pos != -1:
            frag = uri[pos + 1:]
            resource_uri = uri[:pos]
        else:
            frag = None
            resource_uri = uri
        # Return resource from cache if exists
        if not resource_uri in self.cache:
            # Read the resource and resolve any references. Add the result to
            # the cache.
            data = self.read(resource_uri)
            # If no base Uri is set use the prefix of the given Uri
            if self.base_uri is None:
                base_uri = uri[:resource_uri.rfind('/')]
            else:
                base_uri = self.base_uri
            self.cache[resource_uri] = data
            self.resolve_refs(data, base_uri)
        data = self.cache[resource_uri]
        # Return only the requested fragment of the data object (if given).
        # Raises a ValueError if fragment does not exist.
        if not frag is None and frag != '':
            if frag.startswith('/'):
                frag = frag[1:]
            obj = data
            for key in frag.split('/'):
                if key in obj:
                    obj = obj[key]
                else:
                    raise ValueError('unknown fragment: ' + frag)
            return obj
        else:
            return data

    @abstractmethod
    def read(self, uri):
        """Method to read resource at given Uri and return a Json object.
        Implementation depends on the serialization format the resource is
        expected to be in.

        Parameters
        ----------
        uri : string
            Unique resource identifier

        Returns
        -------
        JSON
            Resource content in Json format
        """
        pass

    def resolve_refs(self, obj, base_uri):
        """Replace references in a given Json object by loading the referenced
        resource. Expects references to be dictionaries containing a single
        element '$ref'.

        Parameters
        ----------
        obj : JSON
            Json object
        base_uri : string
            Uri to evaluate references against.

        Returns
        -------
        JSON
            Modified version of the original object where references are
            replaced with their referenced content.
        """
        # Expects a dict object. If no dictionary given returns object as is.
        if type(obj) is dict:
            for key in obj:
                el = obj[key]
                if type(el) is dict:
                    # Test whether the dict is a reference
                    if len(el) == 1 and '$ref' in el:
                        obj[key] = self.load(get_absolute_uri(base_uri, el['$ref']))
                    else:
                        self.resolve_refs(el, base_uri)
                elif type(el) is list:
                    obj[key] = self.resolve_list_refs(el, base_uri)
        return obj

    def resolve_list_refs(self, arr, base_uri):
        """Replace references in a given Json array by loading the referenced
        resource. Expects references to be dictionaries containing a single
        element '$ref'.

        Parameters
        ----------
        arr : JSON
            Json array
        base_uri : string
            Uri to evaluate references against.

        Returns
        -------
        JSON
            Modified version of the original array where references are
            replaced with their referenced content.
        """
        result = []
        for el in arr:
            # Expects a dict object. If no dictionary given returns object as is.
            if type(el) is dict:
                # Test whether the dict is a reference
                if len(el) == 1 and '$ref' in el:
                    result.append(self.load(get_absolute_uri(base_uri, el['$ref'])))
                else:
                    result.append(self.resolve_refs(el, base_uri))
            elif type(el) is list:
                result.append(self.resolve_list_refs(el, base_uri))
            else:
                result.append(el)
        return result


class JSONLoader(ObjectLoader):
    """Implementation of object reader for resources that are expected to be
    in JSON format.
    """
    def __init__(self, base_uri=None):
        """Initialize the super class.

        Parameters
        ----------
        base_uri : string, optional
            Unique resource identifier
        """
        super(JSONLoader, self).__init__(base_uri=base_uri)

    def read(self, uri):
        """Read resource in JSON format and return Json object.

        Parameters
        ----------
        uri : string
            Unique resource identifier

        Returns
        -------
        JSON
            Resource content in Json format
        """
        return json.loads(ResourceReader().read(uri))


class YAMLLoader(ObjectLoader):
    """Implementation of object reader for resources that are expected to be
    in YAML format.
    """
    def __init__(self, base_uri=None):
        """Initialize the super class.

        Parameters
        ----------
        base_uri : string, optional
            Unique resource identifier
        """
        super(YAMLLoader, self).__init__(base_uri=base_uri)

    def read(self, uri):
        """Read resource in YAML format and return Json object.

        Parameters
        ----------
        uri : string
            Unique resource identifier

        Returns
        -------
        JSON
            Resource content in Json format
        """
        return yaml.load(ResourceReader().read(uri))


class ResourceReader(object):
    """Helper class to read the content of a resource for a given Uri. resources
    can be referenced accessed via HTTP or they are files on the local disk.
    """
    def read(self, uri):
        """Read content of a resource at given Uri. Uses urllib2 and should be
        able to read Web resources as well as files on the local disk.

        Raises ValueError if resource is not found or cannot be accessed.

        Parameters
        ----------
        uri : string
            Unique resource identifier

        Returns
        -------
        string
            Content of the resource.
        """
        try:
            return urllib2.urlopen(uri).read()
        except urllib2.HTTPError as ex:
            raise ValueError('[' + uri + ']: ' + ex.read())


# ------------------------------------------------------------------------------
#
# Helper Methods
#
# ------------------------------------------------------------------------------

def extend_with_default(validator_class):
    """Copied from cap-schemas."""
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        if schema.get('title',None)=='Yadage Stage':
            if 'dependencies' in instance and type(instance['dependencies'])==list:
                instance['dependencies'] = {
                    "dependency_type" : "jsonpath_ready",
                    "expressions": instance["dependencies"]
                    }

        if "Scheduler" in schema.get('title',''):
            if(type(instance['parameters'])==dict):
                asarray = []
                for k,v in instance['parameters'].iteritems():
                    if type(v) == dict:
                        v['expression_type'] = 'stage-output-selector'
                    asarray.append({'key':k,'value':v})

                instance['parameters'] = asarray

        for prop, subschema in properties.iteritems():
            if "default" in subschema:
                instance.setdefault(prop, subschema["default"])

        for error in validate_properties(
            validator, properties, instance, schema,
        ):
            yield error

    return validators.extend(
        validator_class, {"properties" : set_defaults},
    )


def get_absolute_uri(base_uri, path):
    """Append path to given Uri. Use urlparse.urljoin to ensure that relative
    path references (i.e., '.' and '..') are handled properly.

    Parameters
    ----------
    base_uri : string
        Unique resource identifier
    path: string
        Relative resource path

    Returns
    -------
    string
        Concatenation of base Uri and path
    """
    uri = base_uri
    # Remove path fragment if present
    pos = path.find('#')
    if pos != -1:
        url_path = path[:pos]
        frag = path[pos:]
    else:
        url_path = path
        frag = ''
    for el in url_path.split('/'):
        if not uri.endswith('/'):
            uri += '/'
        uri = urlparse.urljoin(uri, el)
    # Make sure to attach path fragement
    return uri + frag
