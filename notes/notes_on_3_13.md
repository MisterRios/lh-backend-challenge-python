The readme is missing the documentation on installing the virtual environment. Poking around in the files, it is found in an init.sh file, which is a great idea, but not everyone would be necessarily familiar with this setup.

Also, the python version is not documented anywhere, so when I run the init.sh file, it installs python 3.13, which seems to have a couple of breaking changes involving freezegun.

The python version is not documented anywhere. In the Dockerfile, it uses version 3.9, but in the README, the screen shots make it look like it is running 3.10.9. 

Unless the dev is expected to use pyenv to manage the different versions of python, it makes sense that the most recent version of python will be used, or at the very least, a moderately current version of python. Python 3.9 will lose support this year in October, so it cannot count as current.

When running init.sh, because no specific version has been designated, this will be the case, which will lead to a couple of setup errors. I've seen errors like this many times, but this one, because of the breaking changes in 3.13, requires a bit more time than I was willing to spend setting up a takehome challenge. At some point, I have to complete the requirements. Here is my experience trying to upgrade the app to the current Python. Hopefully the team will upgrade it before end of life for 3.9, or at least upgrade it to 3.12, which, based on this experience, should be easier to upgrade to.



The first error (when running pytest initially):

File "/home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/lib/python3.13/site-packages/pytest_freezegun.py", line 5, in <module>
    from distutils.version import LooseVersion
ModuleNotFoundError: No module named 'distutils'

Okay, a quick google search reveals that this module has been removed in Python 3.12, but you can install setup tools to work around it.

The second error:
File "/home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/lib/python3.13/site-packages/freezegun/api.py", line 70, in <module>
    uuid._load_system_functions()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'uuid' has no attribute '_load_system_functions'

Notice the pattern? It's coming from freezegun. Without checking this error, I first compare the versions of freezegun from requirements-1.2.2 with the current one- 1.5.2

Further research reveals that these private undocumented methods were being removed from uuid anyhow, and the issue was being fixed in freezegun: https://github.com/python/cpython/issues/113308 The freezegun PR solving the issue was merged in 2 March 2024, which means that it would appear in release 1.5.0 from 23 April 2024. Normally I use Poetry to keep my packages up to date, and in this case my first instinct was to just upgrade to the current package 1.5.2, but I decided to see if it would run with the release after they patched the bug.

Upgraded freezegun to 1.5.0 and run it again:
_________________________________________________________________ ERROR collecting app/test_bookings.py _________________________________________________________________
app/test_bookings.py:4: in <module>
    from fastapi.testclient import TestClient
venv/lib/python3.13/site-packages/fastapi/__init__.py:7: in <module>
    from .applications import FastAPI as FastAPI
venv/lib/python3.13/site-packages/fastapi/applications.py:16: in <module>
    from fastapi import routing
venv/lib/python3.13/site-packages/fastapi/routing.py:22: in <module>
    from fastapi import params
venv/lib/python3.13/site-packages/fastapi/params.py:4: in <module>
    from pydantic.fields import FieldInfo, Undefined
venv/lib/python3.13/site-packages/pydantic/__init__.py:2: in <module>
    from . import dataclasses
venv/lib/python3.13/site-packages/pydantic/dataclasses.py:41: in <module>
    from typing_extensions import dataclass_transform
venv/lib/python3.13/site-packages/typing_extensions.py:1174: in <module>
    class TypeVar(typing.TypeVar, _DefaultMixin, _root=True):
E   TypeError: type 'typing.TypeVar' is not an acceptable base type

First google hit leads here: https://github.com/python/typing_extensions/issues/243
This issue is specific to typing_extension 4.5.0, so I'm going to go ahead and upgrade it to 4.6.0, as the issue claims it is fixed in this version.


The next issue seems to be with pydantic:
    update_field_forward_refs(f, globalns=globalns, localns=localns)
venv/lib/python3.13/site-packages/pydantic/typing.py:520: in update_field_forward_refs
    field.type_ = evaluate_forwardref(field.type_, globalns, localns or None)
venv/lib/python3.13/site-packages/pydantic/typing.py:66: in evaluate_forwardref
    return cast(Any, type_)._evaluate(globalns, localns, set())
E   TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'


A stackoverflow page says to just downgrade to python version 3.12.3. Sometimes this is an option, but other times it's not.
Another answerer suggests updating pydantic to v2.7.4. So I'll do this.

Unfortunately, fastapi breaks down: 

ERROR: Cannot install fastapi==0.95.1 and pydantic==2.7.4 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested pydantic==2.7.4
    fastapi 0.95.1 depends on pydantic!=1.7, !=1.7.1, !=1.7.2, !=1.7.3, !=1.8, !=1.8.1, <2.0.0 and >=1.6.2

The commit in which it appears that the change to support v2 is here: https://github.com/fastapi/fastapi/commit/0976185af96ab2ee39c949c0456be616b01f8669
which means we need the next release after 7 July 2023.
Looks like it is release 0.100.0 which mentions Pydantic 2 rewriting its core in Rust: https://github.com/fastapi/fastapi/releases/tag/0.100.0

Okay, changed in requirements, which leads to: 

ERROR: Cannot install -r requirements.txt (line 7) and starlette==0.26.1 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested starlette==0.26.1
    fastapi 0.100.0 depends on starlette<0.28.0 and >=0.27.0


The answer is right here, let's upgrade to starlette 0.27.0

Another easy error: 
ERROR: Cannot install -r requirements.txt (line 1), -r requirements.txt (line 18), -r requirements.txt (line 7) and typing_extensions==4.6.0 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested typing_extensions==4.6.0
    alembic 1.10.4 depends on typing-extensions>=4
    fastapi 0.100.0 depends on typing-extensions>=4.5.0
    pydantic 2.7.4 depends on typing-extensions>=4.6.1


Upgrading typing-extensions to 4.6.1

And finally, a different error:
Building wheels for collected packages: pydantic-core
  Building wheel for pydantic-core (pyproject.toml) ... error
  error: subprocess-exited-with-error
  
  × Building wheel for pydantic-core (pyproject.toml) did not run successfully.
  │ exit code: 1
  ╰─> [13 lines of output]
      Running `maturin pep517 build-wheel -i /home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3 --compatibility off`
      📦 Including license file "/tmp/pip-install-8w5q2kgq/pydantic-core_5616cc870eec40538578dccd878ed506/LICENSE"
      🍹 Building a mixed python/rust project
      🔗 Found pyo3 bindings
      🐍 Found CPython 3.13 at /home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3
      📡 Using build options features, bindings from pyproject.toml
      warning: unused manifest key: lints
      error: package `pydantic-core v2.18.4 (/tmp/pip-install-8w5q2kgq/pydantic-core_5616cc870eec40538578dccd878ed506)` cannot be built because it requires rustc 1.76 or newer, while the currently active rustc version is 1.70.0
      
      💥 maturin failed
        Caused by: Failed to build a native library through cargo
        Caused by: Cargo build finished with "exit status: 101": `env -u CARGO PYO3_ENVIRONMENT_SIGNATURE="cpython-3.13-64bit" PYO3_PYTHON="/home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3" PYTHON_SYS_EXECUTABLE="/home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3" "cargo" "rustc" "--features" "pyo3/extension-module" "--message-format" "json-render-diagnostics" "--manifest-path" "/tmp/pip-install-8w5q2kgq/pydantic-core_5616cc870eec40538578dccd878ed506/Cargo.toml" "--release" "--lib" "--crate-type" "cdylib"`
      Error: command ['maturin', 'pep517', 'build-wheel', '-i', '/home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3', '--compatibility', 'off'] returned non-zero exit status 1
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
  ERROR: Failed building wheel for pydantic-core
Failed to build pydantic-core

A quick check of my version of rust confirms this:
╰─rustc -V
rustc 1.70.0 (90c541806 2023-05-31)

So we run:
╰─ rustup update stable   
check the version:
╰─ rustc -V
rustc 1.87.0 (17067e9ac 2025-05-09)

and then try again but no dice:
Building wheels for collected packages: pydantic-core
  Building wheel for pydantic-core (pyproject.toml) ... error
  error: subprocess-exited-with-error
  
  × Building wheel for pydantic-core (pyproject.toml) did not run successfully.
  │ exit code: 1
  ╰─> [75 lines of output]
      Running `maturin pep517 build-wheel -i /home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3 --compatibility off`
      📦 Including license file "/tmp/pip-install-57nbpdea/pydantic-core_a95137831eec4b598aa299908bb9204e/LICENSE"
      🍹 Building a mixed python/rust project
      🔗 Found pyo3 bindings
      🐍 Found CPython 3.13 at /home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3
      📡 Using build options features, bindings from pyproject.toml
         Compiling autocfg v1.1.0
         Compiling target-lexicon v0.12.9
         Compiling python3-dll-a v0.2.9
         Compiling proc-macro2 v1.0.76
         Compiling unicode-ident v1.0.10
         Compiling once_cell v1.18.0
         Compiling libc v0.2.147
         Compiling heck v0.4.1
         Compiling cfg-if v1.0.0
         Compiling version_check v0.9.4
         Compiling rustversion v1.0.13
         Compiling parking_lot_core v0.9.8
         Compiling smallvec v1.13.2
         Compiling num-traits v0.2.16
         Compiling lock_api v0.4.10
         Compiling num-integer v0.1.45
         Compiling num-bigint v0.4.4
         Compiling memoffset v0.9.0
         Compiling radium v0.7.0
         Compiling static_assertions v1.1.0
         Compiling portable-atomic v1.6.0
         Compiling quote v1.0.35
         Compiling pyo3-build-config v0.21.2
         Compiling scopeguard v1.1.0
         Compiling tinyvec_macros v0.1.1
         Compiling tinyvec v1.6.0
         Compiling syn v2.0.48
         Compiling lexical-util v0.8.5
         Compiling ahash v0.8.10
         Compiling tap v1.0.1
         Compiling memchr v2.6.3
         Compiling serde v1.0.203
         Compiling wyz v0.5.1
         Compiling parking_lot v0.12.1
         Compiling unicode-normalization v0.1.22
         Compiling lexical-parse-integer v0.8.6
         Compiling aho-corasick v1.0.2
         Compiling getrandom v0.2.10
         Compiling serde_json v1.0.116
         Compiling zerocopy v0.7.32
         Compiling unindent v0.2.3
         Compiling indoc v2.0.4
         Compiling pyo3-ffi v0.21.2
         Compiling pyo3 v0.21.2
         Compiling jiter v0.4.1
         Compiling regex-syntax v0.8.2
         Compiling equivalent v1.0.1
         Compiling funty v2.0.0
      error: failed to run custom build command for `pyo3-ffi v0.21.2`
      
      Caused by:
        process didn't exit successfully: `/tmp/pip-install-57nbpdea/pydantic-core_a95137831eec4b598aa299908bb9204e/target/release/build/pyo3-ffi-72b2be2c4850e273/build-script-build` (exit status: 1)
        --- stdout
        cargo:rerun-if-env-changed=PYO3_CROSS
        cargo:rerun-if-env-changed=PYO3_CROSS_LIB_DIR
        cargo:rerun-if-env-changed=PYO3_CROSS_PYTHON_VERSION
        cargo:rerun-if-env-changed=PYO3_CROSS_PYTHON_IMPLEMENTATION
        cargo:rerun-if-env-changed=PYO3_PRINT_CONFIG
        cargo:rerun-if-env-changed=PYO3_USE_ABI3_FORWARD_COMPATIBILITY
      
        --- stderr
        error: the configured Python interpreter version (3.13) is newer than PyO3's maximum supported version (3.12)
        = help: please check if an updated version of PyO3 is available. Current version: 0.21.2
        = help: set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 to suppress this check and build anyway using the stable ABI
      warning: build failed, waiting for other jobs to finish...
      💥 maturin failed
        Caused by: Failed to build a native library through cargo
        Caused by: Cargo build finished with "exit status: 101": `env -u CARGO PYO3_ENVIRONMENT_SIGNATURE="cpython-3.13-64bit" PYO3_PYTHON="/home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3" PYTHON_SYS_EXECUTABLE="/home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3" "cargo" "rustc" "--features" "pyo3/extension-module" "--message-format" "json-render-diagnostics" "--manifest-path" "/tmp/pip-install-57nbpdea/pydantic-core_a95137831eec4b598aa299908bb9204e/Cargo.toml" "--release" "--lib" "--crate-type" "cdylib"`
      Error: command ['maturin', 'pep517', 'build-wheel', '-i', '/home/misterrios/Projects/limehome_takehome/backend-challenge-python/venv/bin/python3', '--compatibility', 'off'] returned non-zero exit status 1
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
  ERROR: Failed building wheel for pydantic-core
Failed to build pydantic-core


At this point, I would probably just use poetry to update all the versions and run the app again.

Instead, I tried to ugrade as many main packages as I could, but only came out with this as requirements: 

alembic==1.16.2
annotated-types==0.7.0
anyio==3.6.2
asgi-lifespan==2.1.0
certifi==2022.12.7
click==8.2.1
exceptiongroup==1.1.1
fastapi==0.115.13
freezegun==1.5.2
greenlet==3.2.3
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.4
iniconfig==2.1.0
Mako==1.2.4
MarkupSafe==2.1.2
packaging==23.1
pluggy==1.6.0
pydantic==2.11.7
pydantic_core==2.33.2
Pygments==2.19.1
pytest==8.4.0
pytest-asyncio==1.0.0
pytest-freezegun==0.4.2
python-dateutil==2.9.0.post0
setuptools==80.9.0
six==1.16.0
sniffio==1.3.0
SQLAlchemy==2.0.41
starlette==0.46.2
tomli==2.2.1
typing-inspection==0.4.1
typing_extensions==4.14.0
uvicorn==0.34.3

Turns out, the tests still won't run:
...
FAILED app/test_bookings.py::test_extend_booking__no_booking__different_unit - pydantic.errors.PydanticSchemaGenerationError: Unable to generate pydantic-core schema for <class 'datetime.date'>. Set `arbitrary_types_allowed...
FAILED app/test_bookings.py::test_extend_booking_too_few_nights - pydantic.errors.PydanticSchemaGenerationError: Unable to generate pydantic-core schema for <class 'datetime.date'>. Set `arbitrary_types_allowed...
FAILED app/test_bookings.py::test_extend_booking_same_number_of_nights - pydantic.errors.PydanticSchemaGenerationError: Unable to generate pydantic-core schema for <class 'datetime.date'>. Set `arbitrary_types_allowed...
========================================================= 13 failed, 55 warnings in 14.48s ==========================================================

The issue seems to be documented here: https://github.com/pydantic/pydantic/discussions/9343
At the end, someone even suggests switching to `time-machine`, a drop-in library by prolific Djangonaut Adam Johnson


I stopped here, because I had spent too much time on setup, and hoped that installing 3.9 via pyenv would allow me to actually begin the challenge.
