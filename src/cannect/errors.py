class AmdDuplicationError(Exception):
    pass

class AmdFormatError(Exception):
    pass

class AmdNotFoundError(Exception):
    pass

class AscetWorkspaceFormatError(Exception):
    pass

class CANDBError(Exception):
    pass

class CANDBDuplicationError(Exception):
    pass

class CANDBMessageNotFound(Exception):
    pass

class CodeBeamerError(Exception):
    pass

class IRFormatError(Exception):
    pass

class SDDError(Exception):
    pass

class SDDLogError(Exception):
    pass

class SDDNotFoundError(FileNotFoundError):
    pass

class SDDOutOfDateError(Exception):
    pass

class SVNError(Exception):
    pass