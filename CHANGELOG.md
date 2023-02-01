# Changelog

## v3.1.0

### Fixes
- CLI: update to be compatible with `aiida-core==2.1` [[#112]](https://github.com/aiidateam/aiida-codtools/commit/112)

### Dependencies
- Add support for Python 3.11 [[#113]](https://github.com/aiidateam/aiida-codtools/commit/113)
- Update requirement to `aiida-core~=2.0` [[#109]](https://github.com/aiidateam/aiida-codtools/commit/109)

### DevOps
- Move the source directory into `src/` [[#110]](https://github.com/aiidateam/aiida-codtools/commit/110)
- Fix the continuous-deployment workflow [[#114]](https://github.com/aiidateam/aiida-codtools/commit/114)


## v3.0.0

### Changes
- Add support for `aiida-core~=2.0` [[48490bf4]](https://github.com/aiidateam/aiida-codtools/commit/48490bf44f63ed1f7383636085ea5eb6d6d3d57e)
- Drop Python 3.6 and 3.7 support [[882a4750]](https://github.com/aiidateam/aiida-codtools/commit/882a47503828d33e851086ccba3fec87c59d66b4)


## v2.2.0

### Changes
- Drop Python 3.5 support [[b6728f0c]](https://github.com/aiidateam/aiida-codtools/commit/b6728f0ceff472511091126e813ab77735c4c2d1)
- Add Python 3.9 and 3.10 support [[c48dc7a1]](https://github.com/aiidateam/aiida-codtools/commit/c48dc7a16d13d07674e17355949ac7743b3e6a95)

### DevOps
- Devops: add GitHub Actions workflow for continuous deployment [[6771fe7b]](https://github.com/aiidateam/aiida-codtools/commit/6771fe7bcf3c8a7ae36028a75921e4974de4efc2)
- Adopt PEP 621 and move fully to `pyproject.toml` for package build specification [[d5baf42c]](https://github.com/aiidateam/aiida-codtools/commit/d5baf42cdb39f577969c2ab3c64d51fbcbeb1167)
- Move build of documentation directly on ReadTheDocs [[c246071c]](https://github.com/aiidateam/aiida-codtools/commit/c246071c3dc9890382412e89af9a60b489844f52)
- CI: update the pre-commit configuration, dropping `prospector`, adding `flynt` and `isort` [[ff82141e]](https://github.com/aiidateam/aiida-codtools/commit/ff82141e894ad926c710f806266cff9d118a561a)
- CI: update the GHA workflow, updating action dependencies and cleaning up unnecessary installs [[a11381be]](https://github.com/aiidateam/aiida-codtools/commit/a11381be8c7977bed1e42155dc22159556d21603)
- Dependencies: update requirements for `sphinx` and `jinja2` for the docs build [[e8f4c537]](https://github.com/aiidateam/aiida-codtools/commit/e8f4c5379bdaa9e8820b9722ed7bfdebc9d6693a)


## v2.1.0

### Changes
- Drop Python 2 support, now only support Python 3.5, 3.6, 3.7 and 3.8 [[#95]](https://github.com/aiidateam/aiida-core/pull/95)
- `CifCleanWorkChain`: use lambdas for ports with node defaults [[#100]](https://github.com/aiidateam/aiida-core/pull/100)

### DevOps
- CI: remove explicit install of system requirements by services [[#104]](https://github.com/aiidateam/aiida-core/pull/104)
- Move CI from Travis to GitHub actions [[#3949]](https://github.com/aiidateam/aiida-core/pull/3949)


## v2.0.0

First release to be compatible with `aiida-core>=1.0.0` and Python 3.
