# django-fly-replay

[![Tests](https://github.com/katiayn/django-fly-replay/actions/workflows/tests.yml/badge.svg)](https://github.com/katiayn/django-fly-replay/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/katiayn/django-fly-replay/branch/main/graph/badge.svg)](https://codecov.io/gh/katiayn/django-fly-replay)

A Django middleware that lets you offload resource-intensive views to isolated,
auto-stopping [Fly Machines](https://fly.io/docs/machines/) - without Celery,
without persistent workers, and without changing your view code.

It's a lightweight alternative to task queues for occasional heavy workloads:
report generation, data exports, ML inference, and similar jobs that are too
slow for a web process but too infrequent to justify a full worker fleet.

## License

MIT