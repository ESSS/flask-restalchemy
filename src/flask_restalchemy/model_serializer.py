from serialchemy import ModelSerializer as SerialchemyModelSerialize


class ModelSerializer(SerialchemyModelSerialize):
    """
    Override serialchemy ModelSerializer to provide legacy hooks before_commit
    and after_commit.

    We have the intent of deprecate these hooks in favor of alternatives like
    SQLAlchemy events and Resource decorators.
    """

    def before_put_commit(self, model, session):
        pass

    def after_put_commit(self, model, session):
        pass

    def before_post_commit(self, model, session):
        pass

    def after_post_commit(self, model, session):
        pass
