There is a gap in the README documentation from where the app is run in
docker, to when the tests are run. Although, yes, most developers will
know how to set up a virtual environment, here there are no suggestions
on how to set up the virtual environment, nor mention of the helper
script `init.sh` which seems to take care of it for the user. Also
missing is what version of python to use. Documentation is sometimes the
last thing to be updated, but here, for a takehome challenge, it would
be great to have a few more clues.

I deduced that the app was using python 3.9 from the Dockerfile. No other
mention of any other python version exists anywhere. So I modified the
init.sh file to specifically use python 3.9 when creating the virtual
environment. Reason being was that it was trying to use my system python-
3.13.3.

As a security note, Python 3.9 is reaching End of Life in October of 2025,
so this takehome test really should be revised to use a specific python
version. Given the changes between Python 3.12 and 3.13 in my other
document, it would make sense to just upgrade all the packages to the
current ones to work with the latest Python version.

Another way to work with the tests would be to use the docker app. For
example, to run pytest:
`docker-compose exec api pytest`

The problem with this approach is that with major changes, one would have
to rebuild the container with:
`docker-compose up --build`
