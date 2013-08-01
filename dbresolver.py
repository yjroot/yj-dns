import os
import time

from twisted.names import dns, common
from twisted.internet import defer
from twisted.python import failure
from twisted.python.compat import execfile

from config import Config

import sqlalchemy
from sqlalchemy import Table, Column, ForeignKey,\
                        Integer, Unicode, UnicodeText, DateTime, Enum, Boolean
from sqlalchemy.sql import functions
import sqlalchemy.orm
import sqlalchemy.ext.declarative

DB_CONFIG = Config('Database')

Session = sqlalchemy.orm.sessionmaker(autocommit=True)
Session.configure(bind=sqlalchemy.create_engine(DB_CONFIG['url']))

Base = sqlalchemy.ext.declarative.declarative_base()

default_ttl = 300

class History(Base):
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True)

    request_at = Column(DateTime(timezone=True), nullable=False, default=functions.now())

    type = Column(Unicode(32), nullable=False)
    name = Column(Unicode(255), nullable=False)

class RecordA(Base):
    __tablename__ = 'A'

    id = Column(Integer, primary_key=True)

    name = Column(Unicode(255), nullable=False, index=True)

    address = Column(Unicode(32), nullable=False)
    ttl = Column(Integer, nullable=True)

    @property
    def record(self):
        return dns.Record_A(self.address, self.ttl or default_ttl)

class RecordCname(Base):
    __tablename__ = 'CNAME'

    id = Column(Integer, primary_key=True)

    name = Column(Unicode(255), nullable=False, index=True)

    cname = Column(Unicode(255), nullable=False)
    ttl = Column(Integer, nullable=True)

    @property
    def record(self):
        return dns.Record_CNAME(self.cname, self.ttl or default_ttl)

def database_init():
    Base.metadata.create_all(sqlalchemy.create_engine(DB_CONFIG['url']))

def database_drop():
    Base.metadata.drop_all(sqlalchemy.create_engine(DB_CONFIG['url']))

class DatabaseAuthority(common.ResolverBase):
    def __init__(self, connection=None):
        common.ResolverBase.__init__(self)
        self._cache = {}

    def __setstate__(self, state):
        self.__dict__ = state

    def _lookup(self, name, cls, type, timeout = None):
        session = Session()
        history = History(type=dns.QUERY_TYPES[type], name=name)
        with session.begin():
            session.add(history)
        def lookup_a(name):
            results = session.query(RecordA).filter(RecordA.name==name).all()
            return [dns.RRHeader(name, dns.A, dns.IN, result.record.ttl, result.record, auth=True) for result in results]
        def lookup_cname(name):
            results = session.query(RecordCname).filter(RecordCname.name==name).all()
            return [dns.RRHeader(name, dns.CNAME, dns.IN, result.record.ttl, result.record, auth=True) for result in results]
        if type == dns.A:
            results = lookup_a(name)
            if results:
                return defer.succeed((results, [], []))
            results = lookup_cname(name)
            for record in results:
                results = results + lookup_a(str(record.payload.name))
            if results:
                return defer.succeed((results, [], []))
            #return defer.fail(failure.Failure(dns.AuthoritativeDomainError(name)))
        return defer.fail(failure.Failure(dns.DomainError(name)))

