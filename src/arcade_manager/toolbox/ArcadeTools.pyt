from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from arcade_manager import Committer, Extractor

from arcpy import Parameter

@dataclass
class Tool:
    label: str = None
    category: str = None
    description: str = None
    canRunInBackground: bool = True
    
    def __post_init__(self):
        if not self.label:
            self.label = self.__class__.__name__
            
    def getParameterInfo(self): ...
    def updateParameters(self, parameters: list[Parameter], messages: list): ...
    def updateMessages(self, parameters: list[Parameter], messages: list): ...
    def isLicensed(self): ...
    def execute(self, parameters: list[Parameter], messages: list): ...
    def postExecute(self, parameters: list[Parameter], messages: list): ...

class ExtractArcade(Tool):
    def __init__(self):
        super().__init__(self)
        
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
        super().__init__(self)
        
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
    
@dataclass
class Toolbox: 
    label: str = "Arcade Toolbox"
    alias: str = "ArcadeToolbox"
    tools: list[Tool] = (ExtractArcade, CommitArcade)