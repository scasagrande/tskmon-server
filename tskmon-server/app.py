#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORTS ####################################################################

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from flask_ripozo import FlaskDispatcher

from ripozo import restmixins, ListRelationship, Relationship
from ripozo.decorators import apimethod
from ripozo.adapters import SirenAdapter, HalAdapter

from ripozo_sqlalchemy import AlchemyManager, SessionHandler

from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/database.db'
db = SQLAlchemy(app)


# DATABASE MODELS ############################################################

class TaskBoard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tasks = relationship('Task', backref='task_board')
    title = db.Column(db.String(50), nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_board_id = db.Column(db.Integer, db.ForeignKey('task_board.id'), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)

db.create_all()

session_handler = SessionHandler(db.session)


# DATA MANAGERS ##############################################################

class TaskBoardManager(AlchemyManager):
    fields = ('id', 'title', 'tasks.id',)
    list_fields = ('id', 'title',)
    update_fields = ('title',)
    model = TaskBoard
    paginate_by = 10


class TaskManager(AlchemyManager):
    fields = ('id', 'task_board_id', 'title', 'description', 'completed',)
    model = Task
    paginate_by = 20


# API RESOURCES ##############################################################

class TaskBoardResource(restmixins.CRUDL):
    manager = TaskBoardManager(session_handler)
    resource_name = 'taskboard'
    pks = ('id',)
    _relationships = (
        ListRelationship('tasks', relation='TaskResource'),
    )

    @apimethod(route='/addtask', methods=['POST'])
    def add_task(cls, request):
        body_args = request.body_args
        body_args['task_board_id'] = request.get('id')
        request.body_args = body_args
        return TaskResource.create(request)


class TaskResource(restmixins.CRUD):
    manager = TaskManager(session_handler)
    resource_name = 'task'
    pks = ('id',)
    _relationships = (
        Relationship(
            'task_board',
            property_map=dict(task_board_id='id'),
            relation='TaskBoardResource'
        ),
    )

dispatcher = FlaskDispatcher(app, url_prefix='/api')
dispatcher.register_adapters(SirenAdapter, HalAdapter)
dispatcher.register_resources(TaskBoardResource, TaskResource)

if __name__ == '__main__':
    app.run(debug=True)
