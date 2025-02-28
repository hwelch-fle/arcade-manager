from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from arcpy import Parameter
from arcade_manager import Committer, Extractor

class Tool:
    def __init__(self):
        self.label: str = None
        self.category: str = None
        self.description: str = None
        self.canRunInBackground: bool = True

    def getParameterInfo(self): ...
    def updateParameters(self, parameters: list[Parameter]): ...
    def updateMessages(self, parameters: list[Parameter]): ...
    def isLicensed(self): return True
    def execute(self, parameters: list[Parameter], messages: list): ...
    def postExecute(self, parameters: list[Parameter], messages: list): ...

class ExtractArcade(Tool):
    def __init__(self):
        super().__init__()
        
        # Override Defaults
        self.label = "Extract Rules"
        self.description = "Extracts arcade scripts from a database and generates a structured directory that can be edited with an IDE"
        
    def getParameterInfo(self):
        database = Parameter(
            name='database',
            displayName='Source Database',
            datatype='DEWorkspace',
        )
        repo = Parameter(
            name='repo',
            displayName='Target Repository',
            datatype='DEFolder',
        )
        return [database, repo]
    
    def execute(self, parameters: list[Parameter], messages) -> None:
        database, repo = parameters
        
        database = Path(database.valueAsText)
        repo = Path(repo.valueAsText)
        
        Extractor(database, repo).extract()
        
class CommitArcade(Tool):
    def __init__(self):
        super().__init__()
        
        # Override Defaults
        self.label = "Commit Rules"
        self.description = "Commits arcade scripts from a structured directory into a database"

    def getParameterInfo(self):
        repo = Parameter(
            name='repo',
            displayName='Source Repository',
            datatype='DEFolder',
        )
        database = Parameter(
            name = 'database',
            displayName= 'Target Database',
            datatype = 'DEWorkspace',
        )
        return [repo, database]
    
    def execute(self, parameters: list[Parameter], messages) -> None:
        repo, database = parameters
        
        repo = Path(repo.valueAsText)
        database = Path(database.valueAsText)
        
        Committer(database, repo).commit()
    
class Toolbox:
    def __init__(self):
        self.label: str = "Arcade Toolbox"
        self.alias: str = "ArcadeToolbox"
        self.tools: list[Tool] = [ExtractArcade, CommitArcade]