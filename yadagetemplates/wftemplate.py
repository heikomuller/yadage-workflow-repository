"""Workflow template loader - Workflow templates contain a unique identifier,
a name, and description. The main component of the template is the workflow
schema. In addition, some workfows may have a list of initial user provided
parameters that are needed to run the workflow.

Workflow schema may be stored in various formats. The source handle is a
description of the schema format that is interpretable by Yadage's workflow
loader.
"""
from abc import abstractmethod
from yadage import workflow_loader
import yadageschemas


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
    def from_json(json_obj, schemadir):
        """Create workflow template instance from a Json object. Expects
        elements for each template attribute that correspond in name to the
        attribute name.

        Parameters
        ----------
        json_obj : JSON
            Json object containing the template information
        schemadir : strings
            Path to Yadage schema directory
        """
        # Get schema source handle and the read the schema information
        schema = SourceHandle.from_json(json_obj['schema']).read(schemadir=schemadir)
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
    def __init__(self):
        """Initialize an empty repository.
        """
        self.db = {}


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

    def load(self, listing, schemadir=yadageschemas.schemadir):
        """Load workflow templates from given listing. Expects a list of
        distionaries that contain source and identifier information for each
        template that is interpretable by Yadage's workflow loader.

        Raises ValueError if templates with duplicate identifiers are present
        in the listing.

        Parameters
        ----------
        listing : list(dict)
            List of workflow template source handle representations
        schemadir : string, optional
            Path to Yadage schema specification directory
        """
        for item in listing:
            wf = WorkflowTemplate.from_json(item, schemadir=schemadir)
            if wf.identifier in self.db:
                raise ValueError('duplicate workflow template: ' + wf.identifier)
            self.db[wf.identifier] = wf

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
    def __init__(self, source, identifier):
        """Initialize the source type and the source specific workflow
        identifier.

        Parameters
        ----------
        source : string
            Source type
        identifier : string
            Source specific identifier
        """
        self.source = source
        self.identifier = identifier

    @staticmethod
    def from_json(obj):
        """Create source handle instance form Json object. Expects an object
        with two elements: 1) source::string, and 2) identifier::string.

        Parameters
        ----------
        obj : JSON
            Json object containing the source handle definition

        Returns
        -------
        SourceHandle
        """
        return SourceHandle(obj['source'], obj['identifier'])

    def read(self, schemadir=None, validate=True):
        """ Reads the template schema from the given source.

        Returns
        -------
        JSON
            Json representation of the the workflow template schema
        """
        return workflow_loader.workflow(
            self.identifier,
            toplevel=self.source,
            schemadir=schemadir,
            validate=validate
        )
