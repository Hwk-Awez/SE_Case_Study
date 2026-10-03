"""
Multi-Database Router
=====================
Implements separation of concerns between:
1. Python's built-in SQLite database ('default') for authentication, users, sessions, and admin.
2. Supabase PostgreSQL database ('supabase') for the software component catalogue assets,
   categories, reuse records, usage metrics, and query logs.
"""


class DatabaseRouter:
    """
    A router to control all database operations on models in the
    'components' application versus the authentication and admin frameworks.
    """
    route_app_labels = {'components'}
    auth_app_labels = {'auth', 'contenttypes', 'sessions', 'admin'}

    def db_for_read(self, model, **hints):
        """
        Attempts to read components models go to 'supabase', auth models to 'default'.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'supabase'
        elif model._meta.app_label in self.auth_app_labels:
            return 'default'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write components models go to 'supabase', auth models to 'default'.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'supabase'
        elif model._meta.app_label in self.auth_app_labels:
            return 'default'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in components is associated with user auth.
        """
        if (
            obj1._meta.app_label in (self.route_app_labels | self.auth_app_labels) and
            obj2._meta.app_label in (self.route_app_labels | self.auth_app_labels)
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the components app only appears in the 'supabase' database,
        and auth/sessions only appear in the 'default' SQLite database.
        """
        if app_label in self.route_app_labels:
            return db == 'supabase'
        elif app_label in self.auth_app_labels:
            return db == 'default'
        return db == 'default'
