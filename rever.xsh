$PROJECT = 'flask-rest-orm'
$GITHUB_ORG = 'ESSS'
$GITHUB_REPO = 'flask-rest-orm'

$ACTIVITIES = [
              'version_bump',
              'tag',
              'push_tag',
              'pypi',
              'conda_forge',
              'ghrelease',
               ]


$VERSION_BUMP_PATTERNS = [
                         ('setup.py', 'version\s*=.*,', "version='$VERSION',")
                         ]

$TAG_TEMPLATE = 'v$VERSION'
$GHRELEASE_NAME = 'v$VERSION'

$PYPI_BUILD_COMMANDS = ('sdist', 'bdist_wheel')