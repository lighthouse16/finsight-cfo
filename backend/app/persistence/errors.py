class PersistenceConfigurationError(ValueError):
    """
    Raised when the persistence configuration is invalid or missing.
    """
    pass

class PersistenceAdapterNotImplementedError(NotImplementedError):
    """
    Raised when the requested persistence adapter has not been implemented.
    """
    pass
