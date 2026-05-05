from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        if not hasattr(UserModel, 'school'):
            UserModel.add_to_class(
                'school',
                property(
                    lambda user: (
                        getattr(getattr(user, 'tenant_profile', None), 'school', None)
                        if getattr(user, 'is_authenticated', False)
                        else None
                    )
                ),
            )
