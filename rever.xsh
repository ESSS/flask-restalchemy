# Some requirements to use rever in this project:
#
# - Set GitHub to work using ssh protocol
# - Define a .pypirc file on $HOME (so rever can upload release packages)

$PROJECT = 'flask-restalchemy'
$GITHUB_ORG = 'ESSS'
$GITHUB_REPO = 'flask-restalchemy'

$ACTIVITIES = [
  'version_bump',
  'changelog',
  'tag',
  'push_tag',
  'pypi',
  'conda_forge',
  'ghrelease',
]

$VERSION_BUMP_PATTERNS = [('setup.py', 'version\s*=.*,', "version='$VERSION',")]

$CHANGELOG_FILENAME = 'CHANGELOG.rst'

$TAG_TEMPLATE = 'v$VERSION'
$GHRELEASE_NAME = 'v$VERSION'

$PYPI_BUILD_COMMANDS = ('sdist', 'bdist_wheel')

$PYTHON = 'python'  # Workarround for regro/rever#121

$CONDA_FORGE_SOURCE_URL = 'https://github.com/$GITHUB_ORG/$GITHUB_REPO/archive/v$VERSION.tar.gz'  # Workarround for regro/rever#122
