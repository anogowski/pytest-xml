rm -rf dist/
py -m build
py -m twine check dist/*.whl