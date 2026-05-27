from apps.tests.models import TestApplication


def create_test_application(**data) -> TestApplication:
    if data.get("status") is None:
        data.pop("status", None)
    return TestApplication.objects.create(**data)


def update_test_application(application: TestApplication, **data) -> TestApplication:
    for field, value in data.items():
        setattr(application, field, value)
    application.save()
    return application
