import ckan.model


def upgrade(migrate_engine):
    migrate_engine.execute(
        '''
        ALTER TABLE "user" ADD COLUMN "state" text NOT NULL DEFAULT '{0!s}'
        '''.format(ckan.model.State.ACTIVE)
    )
