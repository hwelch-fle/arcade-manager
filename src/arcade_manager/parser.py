from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal, Optional
from tempfile import TemporaryDirectory
import json
import builtins

from arcpy import (
    Exists,
    AddMessage,
    AddWarning,
    AddError,
)
from arcpy.da import Describe
from arcpy.management import (
    GenerateSchemaReport, 
    AlterAttributeRule, 
    AddAttributeRule, 
    DeleteAttributeRule,
)

CalculationType = Literal['esriARTCalculation', 'esriARTValidation']
TriggerEvent = Literal['esriARTEUpdate', 'esriARTEInsert', 'esriARTEDelete']

# Override print so messages can be sent to Pro as well
def print(*values: object,
          sep: str = " ",
          end: str = "\n",
          file = None,
          flush: bool = False,
          severity: Literal['INFO', 'WARNING', 'ERROR'] = None):
    """ Print a message to the ArcGIS Pro message queue and stdout
    set severity to 'WARNING' or 'ERROR' to print to the ArcGIS Pro message queue with the appropriate severity
    """

    # Print the message to stdout
    # MessgeFunctions now print to stdout
    #builtins.print(*values, sep=sep, end=end, file=file, flush=flush)
    
    end = "" if end == '\n' else end
    message = f"{sep.join(map(str, values))}{end}"
    # Print the message to the ArcGIS Pro message queue with the appropriate severity
    if not severity:
        severity = 'INFO'
    match severity:
        case "WARNING":
            AddWarning(f"{message}")
        case "ERROR":
            AddError(f"{message}")
        case "INFO":
            AddMessage(f"{message}")
        case _:
            raise ValueError(f"Invalid severity '{severity}'")
    return

@dataclass
class Rule:
    id: int
    name: str
    type: CalculationType
    evaluationOrder: int
    fieldName: str
    subtypeCode: int
    description: str
    errorNumber: int
    errorMessage: str
    userEditable: bool
    isEnabled: bool
    referencesExternalService: bool
    excludeFromClientEvaluation: bool
    scriptExpression: str
    triggeringEvents: list[TriggerEvent]
    checkParameters: dict
    category: int
    severity: int
    tags: str
    batch: bool
    requiredGeodatabaseClientVersion: str
    creationTime: int
    triggeringFields: list[str]
    _parent: Path = field(compare=False)
    
    @property
    def safe_name(self) -> str:
        """Sanitize the rulename so it can be used in a filepath"""
        safe_name = self.name
        illegal = {'<', '>', ':', '"', '\\', '/', '|', '?', '*'}
        for char in self.name:
            if char in illegal:
                safe_name = safe_name.replace(char, '_')
                print(f"Rule {self.name} contains illegal character '{char}', replacing with '_'", severity='WARNING')
        return safe_name
    
    @property
    def translated_type(self) -> str:
        if 'Calculation' in self.type:
            return 'CALCULATION'
        if 'Validation' in self.type:
            return 'VALIDATION'
        if 'Constraint' in self.type:
            return 'CONSTRAINT'
        else:
            raise ValueError(f"Invalid type '{self.type}' for rule '{self.name}'")
    
    @property
    def translated_events(self) -> list[str]:
        events = []
        for event in self.triggeringEvents:
            if 'Insert' in event:
                events.append('INSERT')
            if 'Update' in event:
                events.append('UPDATE')
            if 'Delete' in event:
                events.append('DELETE')
        return events
    
    def _convert_flag(self, flag: int) -> int | None:
        if flag < 0:
            return None
        else:
            return flag
    
    def extract(self, parent_path: Path) -> None:
        parent_path = Path(parent_path) / self.safe_name
        _copy = self.__dict__.copy()
        
        script = _copy.pop('scriptExpression')
        
        # Remove the parent path so it doesn't get written to the config file
        _copy.pop('_parent')
        script_file = parent_path / f"{parent_path.name}.js"
        
        config = json.dumps(_copy, indent=2)
        config_file = parent_path / f"config.json"
        
        parent_path.mkdir(exist_ok=True, parents=True)
        script_file.open(mode='w').write(script)
        config_file.open(mode='w').write(config)
    
    def _delete(self, parent_path: Path) -> None:
        # Move delete to its own function so rules can delete themselves
        parent_path = Path(parent_path)
        parent_name = parent_path.name
        try:
            DeleteAttributeRule(
                in_table=str(parent_path), 
                names=[self.name],
            )
            print(f"Deleted rule {self.name} from {parent_name}", severity='INFO')
        except Exception as e:
            print(
                f"Failed to delete rule {self.name} from {parent_name}\n"
                f"{e}", severity='ERROR'
            )
    
    def _insert(self, parent_path: Path) -> None:
        parent_path = Path(parent_path)
        parent_name = parent_path.name
        try:
            AddAttributeRule(
                in_table=str(parent_path),
                name=self.name,
                type=self.translated_type,
                script_expression=self.scriptExpression,
                is_editable=self.userEditable*'EDITABLE' or 'NONEDITABLE',
                triggering_events=self.translated_events,
                error_number=self._convert_flag(self.errorNumber),
                error_message=self.errorMessage,
                description=self.description,
                subtype=self._convert_flag(self.subtypeCode),
                field=self.fieldName,
                exclude_from_client_evaluation=self.excludeFromClientEvaluation*'EXCLUDE' or 'INCLUDE',
                batch=self.batch*'BATCH' or 'NOT_BATCH',
                severity=self._convert_flag(self.severity),
                tags=self.tags,
                triggering_fields=self.triggeringFields,
            )
            print(f"Added rule {self.name} to {parent_name}", severity='INFO')
        except Exception as e:
            print(
                f"Failed to add rule {self.name} to {parent_name}\n"
                f"{e}", severity='ERROR'
            )
    
    def _update(self, parent_path: Path) -> None:
        parent_path = Path(parent_path)
        parent_name = parent_path.name
        try:
            AlterAttributeRule(
                in_table=str(parent_path),
                name=self.name,
                description=self.description,
                error_number=self._convert_flag(self.errorNumber),
                error_message=self.errorMessage,
                tags=self.tags or 'RESET',
                triggering_events=self.translated_events,
                script_expression=self.scriptExpression,
                exclude_from_client_evaluation=self.excludeFromClientEvaluation*'EXCLUDE' or 'INCLUDE',
                triggering_fields=self.triggeringFields,
            )
            print(f"Updated rule {self.name} in {parent_name}", severity='INFO')
        except Exception as e:
            print(
                f"Failed to update rule {self.name} in {parent_name}\n"
                f"{e}", severity='ERROR'
            )
    
    def commit(self, parent_path: Path, existing: dict[int, Rule], delete=False) -> bool:
        parent_path = Path(parent_path)
        parent_name = parent_path.name
        if not Exists(str(parent_path)):
            print(f"{parent_name} does not exist in target database, skipping", severity='WARNING')
            return False
        
        # Skip if the rule is already in the database and up to date
        if self.id in existing and self == existing[self.id]:
            return False
        
        if delete:
            # Delete rule
            self._delete(parent_path)
            return True
        
        if self.id not in existing:
            # Insert new rule
            self._insert(parent_path)
            return True
                
        else:
            # Alter existing rule
            self._update(parent_path)
            return True

@dataclass
class Dataset:
    name: str
    datasets: Optional[list[Dataset]]
    rules: Optional[list[Rule]]
    _relpath: Optional[str] = None
    
    @property
    def path(self) -> str:
        return self._relpath or self.name
    
    @property
    def safe_name(self) -> str:
        """Sanitize the dataset name so it can be used in a filepath"""
        safe_name = self.name
        illegal = {'<', '>', ':', '"', '\\', '/', '|', '?', '*'}
        for char in self.name:
            if char in illegal:
                safe_name = safe_name.replace(char, '_')
                print(
                    f"Dataset {self.name} contains illegal character '{char}'"
                    f", replacing with '_'", severity='WARNING')
        return safe_name
    
    def extract(self, path: Path) -> None:
        path = Path(path)
        print(f"Extracting Rules in {self.name} to {path.name}", severity='INFO')
        for ds in self.datasets or []:
            # Continue the recursion
            ds.extract(path / ds.safe_name)
        for rule in self.rules or []:
            # Only write out Datasets that have rules
            rule.extract(path)
    
    def commit(self, path: Path, existing: dict[int, Rule]) -> None:
        # Anchor point (<database>\<recursively\rebuilt\paths>)
        path = Path(path)
        # Recurse
        for ds in self.datasets or []:
            ds.commit(path / ds.name, existing=existing)
                        
        # Commit all rules found in tree
        updates = sum(rule.commit(path, existing=existing) for rule in self.rules or [])
        if updates:
            print(f"Committed {updates} changes in {self.name}", severity='INFO')
            print("-"*50, severity='INFO')
    
    def __getitem__(self, key: str):
        for dataset in self.datasets or []:
            if dataset.name == key:
                return dataset
        for rule in self.rules or []:
            if rule.name == key:
                return rule
        
        raise KeyError(f"No '{key}' in '{self.name}'")
 
class Extractor:
    """Extract rules from a database into a directory structure
    
    Usage:
        >>> Extractor(Path(<Database>), Path(<Repo Target>))
        <Messages>
    """
    def __init__(self, database: Path, repo: Path):
        self.database = Path(database)
        self.repo: Path = Path(repo) if repo else None
        self.rules: dict[int, Rule] = {}
        
        with TemporaryDirectory() as schema_out:
            out_path = Path(schema_out) / 'schema.json'
            GenerateSchemaReport(
                in_dataset=str(self.database),
                name=out_path.name,
                out_location=schema_out,
                formats=['JSON'],
            )
            self.schema: Dataset = self._read(json.loads(out_path.open().read()))
            
            # Because GenerateSchemaReport will strip $datastore names and replace
            # them with GUIDs, we need to do a second pass to re-extract the script
            # text using da.Describe
            self._patch_scripts(self.schema, self.database)
        
    def _read(self, schema: dict) -> Dataset:
        return Dataset(
            name=schema['name'],
            datasets=[
                self._read(dataset)
                for dataset in schema['datasets']
                ] if 'datasets' in schema else None,
            rules=[
                Rule(**rule, **{'_parent': Path(schema['catalogPath'])})
                for rule in 
                schema['attributeRules']
                ] if 'attributeRules' in schema else None,
            _relpath=Path(schema['catalogPath']),
        )
        
    def _patch_scripts(self, parent_dataset: Dataset, path: Path) -> None:
        # If the GenerateSchemaReport function is patched to not scrub datastore
        # names, this pass can be skipped
        path = Path(path)
        if parent_dataset.rules:
            scripts = {
                rule['name']: rule['scriptExpression']
                for rule in Describe(str(path))['attributeRules']
            }
            for name, script in scripts.items():
                rule = parent_dataset[name]
                rule.scriptExpression = script
                # Register the Rule
                # If this pass is removed, this needs to be moved to _read()
                # Or this pass will be renamed '_register_rules' and the Describe
                # Call will be removed
                self.rules[rule.id] = rule
        
        for child_dataset in parent_dataset.datasets or []:
            self._patch_scripts(child_dataset, path/child_dataset.name)
            
    def extract(self):
        if not self.repo:
            raise AttributeError(f"Can't extract a when no outpath is specified")
        self.schema.extract(self.repo)
        print(f"Extracted rules from {self.database.name} to {self.repo.name}", severity='INFO')
            
class Committer:
    """Commit an Extracted codebase back to a database
    
    Usage:
        >>> Commiter(Path(<Database>), Path(<Rule Repo>)).commit()
        <Messages>
    """
    def __init__(self, database: Path, repo: Path) -> None:
        self.database = Path(database)
        self.rules: dict[int, Rule] = {}
        self.repo = Path(repo)
        
        # Load current schema so only changed rules are applied
        self._current_state = Extractor(self.database, repo=None)
        self.existing = self._current_state.rules
        
        self.schema = self._load(Path(repo))
              
    def _get_rule(self, config_file: Path) -> Rule:
        # Get containing folder
        rule_dir = config_file.parent
        # Get the parent dataset
        parent = rule_dir.parent
        # Find script file
        script_file = next(rule_dir.glob('*.js'))
        # Load Config
        config = json.loads(config_file.open().read())
        # Load Script
        script = script_file.open().read()
        # Inject script
        config['scriptExpression'] = script
        # Construct Rule object
        rule = Rule(**config, **{'_parent': parent.relative_to(self.repo)})
        # Register the rule
        self.rules[rule.id] = rule
        return rule
       
    def _load(self, path: Path) -> Dataset:
        # This is some heavy duty recursive comprehension, so I tried my best to
        # explain it.    
        return Dataset(
            name=path.name,
            datasets=[
                self._load(dataset) # Load the dataset
                
                for dataset in path.iterdir() # For each dataset in the path
                if dataset.is_dir() # If the dataset is a directory
                
                and not any(item.is_file() for item in dataset.iterdir()) # With no files
            ],
            rules=[
                self._get_rule(file) # Construct rule from config path
                
                for dataset in path.iterdir() # For each folder in path
                if any(item.is_file() for item in dataset.iterdir()) # That has files
                
                for file in dataset.iterdir() 
                if file.name == 'config.json' # One of which is config.json
            ],
            _relpath=path.relative_to(self.repo) if path != self.repo else self.repo,
        )
        
    def commit(self):
        # Anchor the schema to the target database
        # existing rules are passed so only changed rules are applied
        # this saves a lot of time
        self.schema.commit(self.database, existing=self.existing or {})
        for rule in self.existing.values():
            if rule.id not in self.rules:
                rule.commit(self.database/rule._parent, existing=self.existing, delete=True)  
        print(f"Commit to {self.database.name} complete", severity='INFO')
            