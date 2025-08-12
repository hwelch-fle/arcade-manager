from __future__ import annotations
from pathlib import Path

from arcpy import Parameter
from arcpy.mp import ArcGISProject
from arcade_manager import Committer, Extractor, print


class Sync:
    def __init__(self):

        self.project = ArcGISProject("CURRENT")
        self.repo_path = Path(self.project.homeFolder) / "arcade_rules"
        self.repo_path.mkdir(exist_ok=True)

        self.repos = {
            repo.name: repo
            for repo in self.repo_path.iterdir()
            if repo.is_dir() and not repo.name.startswith(".")
        }

        self.repos["origin"] = Path(
            r"S:\Projects\Ezee Fiber\_ArcGIS Setup\Template\\{Market} {FDA} - v1.17\arcade_rules\ezee-arcade"
        )

        self.databases = {
            db.name: db for db in Path(self.project.homeFolder).glob("*.gdb")
        }
        # Override Defaults
        self.label = "Sync Rules"
        self.description = (
            "Syncs arcade scripts between a database and a structured directory"
        )

    def getParameterInfo(self):
        database = Parameter(
            name="database",
            displayName="Target Database",
            datatype="GPString",
            parameterType="Required",
        )
        database.filter.list = list(self.databases.keys())
        if "LLD_Design.gdb" in self.databases.keys():
            database.value = "LLD_Design.gdb"

        repo = Parameter(
            name="repo",
            displayName="Target Repository",
            datatype="GPString",
            parameterType="Required",
        )
        repo.filter.list = list(self.repos.keys())
        repo.value = "origin"

        direction = Parameter(
            name="direction",
            displayName="Direction",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        direction.filter.list = ["Database -> Repo", "Repo -> Database"]
        direction.value = "Repo -> Database"

        return [database, repo, direction]

    def execute(self, parameters: list[Parameter], messages) -> None:
        database_param, repo_param, direction_param = parameters

        database = self.databases.get(database_param.valueAsText)
        repo = self.repos.get(repo_param.valueAsText)
        direction = direction_param.valueAsText
        if direction == "Database -> Repo":
            # Create a new repo if it doesn't exist
            if not repo:
                print(f"Creating new repo at {self.repo_path / repo_param.valueAsText}")
                repo = self.repo_path / repo_param.valueAsText
                repo.mkdir()

            print(f"Syncing rules from {database.name} to {repo.name}")
            Extractor(database, repo).extract()

        elif direction == "Repo -> Database":
            # Ensure the repo exists
            if not repo:
                print(f"Invalid Repo: {repo_param.valueAsText}", severity="ERROR")
                return

            print(f"Syncing rules from {repo.name} to {database.name}")
            Committer(database, repo).commit()
        else:
            # This should never happen
            print(f"Invalid Sync direction: {direction}", severity="ERROR")


class Toolbox:
    def __init__(self):
        self.label: str = "Arcade Toolbox"
        self.alias: str = "ArcadeToolbox"
        self.tools: list = [Sync]
