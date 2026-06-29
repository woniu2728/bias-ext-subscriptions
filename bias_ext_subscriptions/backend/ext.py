from bias_ext_subscriptions.backend.extenders import (
    event_extenders,
    forum_extenders,
    frontend_extenders,
    lifecycle_extenders,
    optional_integration_extenders,
    resource_extenders,
    search_extenders,
)


def extend():
    return [
        *frontend_extenders(),
        *forum_extenders(),
        *search_extenders(),
        *resource_extenders(),
        *event_extenders(),
        *optional_integration_extenders(),
        *lifecycle_extenders(),
    ]
