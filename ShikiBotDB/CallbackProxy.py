import logging
from datetime import timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ShikiBotDB import Callback


class CallbackProxy:
    """
    This class gives some functionality to work with DB
    How to use:
    - Create CallbackProxy object than work with DB, but...
    have in mind that you need to create new object for every thread
    one object can't work in defferent threads
    """
    ENGINE = create_engine('sqlite:///callbacks')

    def __init__(self):
        Session = sessionmaker(bind=self.ENGINE)
        self.session = Session()

    def add_callback(self, chat_id, title_name, title_score, title_synopsis, title_genres):
        """
        Adds record to the Callbacks table.
        Returns this record's id.
        """
        callback = Callback(chat_id,
                            title_name,
                            title_score, 
                            title_synopsis,
                            self.get_genres_ready(title_genres))
        self.session.add(callback)
        self.session.commit()
        # logging.debug('Callback record created.')
        return callback.id

    def get_callback_by_id(self, _id):
        """
        Return the Callback(class) object with given id
        if previous not exists returns None
        """
        query = self.session.query(Callback).filter(Callback.id == _id)
        # logging.debug('Got the id from get_callback_id')
        return query.first()

    def delete_old_callbacks(self, days=1, hours=0, minutes=0):
        """
        Delete callbacks that older than given number of
        days + hours + minutes
        Returns deleted callback.
        """
        query = self.session.query(Callback).filter(
                Callback.message_datetime >= timedelta(days=days,
                                                       hours=hours,
                                                       minutes=minutes)
        )
        self.session.delete(query)
        self.session.commit()
        # logging.debug('deleted_all_callbacks was called')
        return query.first()

    @staticmethod
    def get_genres_ready(genres):
        """
        Remake genres list into string
        Example:
        In: ['first', 'second', 'third']
        Out: 'first, second, third'
        """
        return ', '.join(genres)

    def __del__(self):
        self.session.close()
