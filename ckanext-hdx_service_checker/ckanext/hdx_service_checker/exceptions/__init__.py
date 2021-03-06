
class CheckException(Exception):
    def __init__(self, message, exceptions=None):

        if exceptions is None:
            exceptions = []
        super(Exception, self).__init__(message)

        self.errors = exceptions


class ParamMissingException(CheckException):
    type = 'config-param-missing'

class NonExistentRuntimeVariableException(CheckException):
    type = 'config-param-missing'