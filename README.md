# fred-oss

This is the open-sourced FRED package by the Fahera Research, Education, and Development Team.

## Installation

For local installation, clone the package, go to the root (e.g., `cd fred-oss`) and execute:

```
$ pip install -e fred
```
* General form: `pip install -e path/to/fred`

For development, we recommend installing the development dependencies:
* `pip install -r fred/requirements-develop.txt`

To install via pypi (currently unsupported) just use:
```
$ pip install fred-oss
```

You can optionally specify 'dependency tags' via the following pattern:
```
$ pip install 'fred-oss[<tag-1>,<tag-2>,...]'
```
* `<tag-i>` represents a valid dependency tag (drop the `<` and `>`).
* You can specify one or more dependency tags.

## How to use `fred-project`?

Fred projects are extensions to this implementation such that the implementation is incorporated into the
main python package namespace and can complement the implementation.
Multiple projects could be installed into the same runtime.

For example, installing a local fred project named `hello_world`:
* `pip install -e path/to/hello_world`

You should be able to access the namespace:

```python
from fred.proj.hello_world.utils import hello

hello()
```

Notice the use of `fred.proj` as the generic project namespace; all installed projects should be availabie as submodules.

If the project has setup a CLI interface, you should be able to run:
```
$ fred.proj example <command> <args>
```
* Altenatively: `fred.example <command> <args>`

## How to create your own fred-projects?

Fred projects should implement a very specific template and interface. You can get a ready-to-go project by running:

```
$ fred init --target_dirpath <path/to/target-dir> --name <project-name>
```
* Example: `fred init --target_dirpath . --name demo

You should be able to install and execute a command to verify:
* `pip install -e path/to/target-dir/project-name`
* `fred.proj <project-name> version`


