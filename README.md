# arcade-manager
A simple management toolset that allows you to extract and re-insert Arcade rules into file databases

## Installation
```bash
git clone https://github.com/hwelch-fle/arcade-manager.git
cd arcade-manager
pip install .
```
**NOTE:** `arcpy` is required to run this toolset. If you are not using an ArcGIS Pro Python environment, you will need to add the `arcpy` module to your Python environment.

## Usage with Pro
This package comes with a `toolbox` that can be added to ArcGIS Pro. To do this, simply run the following command:
```bash
python -m arcade_manager init -t "path/to/your/project"
```
This will make a copy of the package at the specified location. You can then add the toolbox to your project by right-clicking on the `Toolboxes` folder in the `Catalog` pane and selecting `Add Toolbox...`. Navigate to the location of the toolbox and select it.
There are 2 tools available in the toolbox:
- Extract Rules
- Commit Rules

These tools are the same as the command line tools, but are available within ArcGIS Pro. With your toolbox copy, you can also add additional tools and hardcode the paths to your database and repo in the toolbox.

**WARNING** It seems that with more complex datasets, running `Commit` through the tool will cause ArcPro to crash. It's probably best to run the CLI tool or just use a python terminal if you need to manage a database with more than ~50 rules

```python
... snip ...
class ExtractArcade(Tool):
    ... snip ...
    def getParameterInfo(self):
        database = Parameter(
            ... snip ...
        database.value = "path/to/your/database.gdb"
        
        repo = Parameter(
            ... snip ...
        repo.value = "path/to/output/repo"
    ...
```
Same setup for the `CommitArcade` class.

## Usage
```bash
>>> arcade-manager extract --database "path/to/your/database.gdb" --repo "path/to/output/repo"
```

## Extracted Folder Structure
```
path/to/output/repo
├── Dataset1
│   ├── FeatureClass1
│   │   ├── Rule1
│   │   │   ├── config.json
│   │   │   └── Rule1.js
|   |   └── Rule2
│   │       ├── config.json
│   │       └── Rule2.js
│   └── FeatureClass2
│       ├── Rule1
│       │   ├── config.json
│       │   └── Rule1.js
│       └── Rule2
│           ├── config.json
│           └── Rile2.js
...
```

## Using with Git
When running an extraction, it's best to extract them to a directory within a git repository. This allows
you to manage multiple extractions using git and re-commit to a database as needed.

```bash
cd path/to/output/repo
git init
arcade-manager extract --database "path/to/your/database.gdb" --repo "path/to/output/repo/database_rules"
git add .
git commit -m "Initial extraction"
... <make your changes>
arcade-manager commit --database "path/to/your/database.gdb" --repo "path/to/output/repo/database_rules"
```
