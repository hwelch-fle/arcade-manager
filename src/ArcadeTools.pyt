from __future__ import annotations
from pathlib import Path

from arcpy import Parameter
from arcpy.mp import ArcGISProject
from arcade_manager import Committer, Extractor, print

class Tool:
    def __init__(self):
        self.label: str = None
        self.category: str = None
        self.description: str = None
        self.canRunInBackground: bool = True
        
        self.repo_path: Path = Path(r'<Path To Repo>')
        self.project = ArcGISProject('CURRENT')
        if not self.repo_path.exists():
            self.repo_path = Path(self.project.homeFolder) / 'arcade_rules'
            self.repo_path.mkdir(exist_ok=True)
        
        self.repos = {
            repo.name: repo
            for repo in self.repo_path.iterdir()
            if repo.is_dir() and not repo.name.startswith('.')
        }
        
        self.databases = {
            db.name: db
            for db in Path(self.project.homeFolder).glob('*.gdb')
        }

    def getParameterInfo(self): ...
    def updateParameters(self, parameters: list[Parameter]): ...
    def updateMessages(self, parameters: list[Parameter]): ...
    def isLicensed(self): return True
    def execute(self, parameters: list[Parameter], messages: list): ...
    def postExecute(self, parameters: list[Parameter], messages: list): ...

class Sync(Tool):
    def __init__(self):
        super().__init__()
        
        # Override Defaults
        self.label = "Sync Rules"
        self.description = "Syncs arcade scripts between a database and a structured directory"
        
    def getParameterInfo(self):
        database = Parameter(
            name='database',
            displayName='Target Database',
            datatype='GPString',
            parameterType='Required',
        )
        database.filter.list = list(self.databases.keys())
    
        repo = Parameter(
            name='repo',
            displayName='Target Repository',
            datatype='GPString',
            parameterType='Required',
        )
        repo.filter.list = list(self.repos.keys())
        
        direction = Parameter(
            name='direction',
            displayName='Direction',
            datatype='GPString',
            parameterType='Optional',
            direction='Input',
        )
        direction.filter.list = ['Database -> Repo', 'Repo -> Database']
        direction.value = 'Database -> Repo'
        
        return [database, repo, direction]
    
    def execute(self, parameters: list[Parameter], messages) -> None:
        database, repo, direction = parameters
        
        database = self.databases.get(database.valueAsText)
        repo = self.repos.get(repo.valueAsText)
        direction = direction.valueAsText
        
        if direction == 'Database -> Repo':
            print(f"Syncing rules from {database.name} to {repo.name}")
            Extractor(database, repo).extract()
        elif direction == 'Repo -> Database':
            print(f"Syncing rules from {repo.name} to {database.name}")
            Committer(database, repo).commit()
        else:
            # This should never happen
            print(f"Invalid Sync direction: {direction}", severity='ERROR')
    
class Toolbox:
    def __init__(self):
        self.label: str = "Arcade Toolbox"
        self.alias: str = "ArcadeToolbox"
        self.tools: list[Tool] = [Sync]
