from datetime import datetime
from hashlib import md5

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

users_to_groups = db.Table('users_to_groups',
    db.Column('member_id', db.ForeignKey('user.id')),
    db.Column('group_id', db.ForeignKey('group.id'))
)

tasks_to_groups = db.Table('tasks_to_groups',
    db.Column('task_id', db.ForeignKey('task.id')),
    db.Column('group_id', db.ForeignKey('group.id')),
    db.PrimaryKeyConstraint('task_id', 'group_id')
)

taskholders = db.Table('tasks_to_users',
    db.Column('user_id', db.ForeignKey('user.id')),
    db.Column('task_id', db.ForeignKey('task.id')),
    db.PrimaryKeyConstraint('user_id', 'task_id')
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='author', lazy='dynamic')
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    about_me = db.Column(db.String(140))
    age = db.Column(db.Integer)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    groups = db.relationship(
        'Group', secondary=users_to_groups,
        backref='members')
    my_groups = db.relationship('Group', backref='owner')
    accounts = db.relationship('Account',  uselist=False, backref='username')
    assigned_tasks = db.relationship(
        'Task', secondary=taskholders,
        backref='holders')

    

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_role(self, rolename):
        role = Role.query.filter_by(rolename=rolename).first()
        self.role = role

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def new_group(self, groupname, description=None):
        group = Group(groupname=groupname, owner_id = self.id, description=description)
        db.session.add(group)
        group.members.append(self)


    def new_task(self, body, groupname=None):
        task = Task(body=body, user_id=self.id)
        db.session.add(task)
        if groupname is not None:
            group = Group.query.filter_by(groupname=groupname).first()
            task.groups.append(group)

    def create_account(self, balance=None):
        account = Account(user_id=self.id, balance=balance)
        db.session.add(account)
                  

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    taskname = db.Column(db.String(35))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gold = db.Column(db.Integer)
    team = db.Column(db.Integer, default=1)
    groups = db.relationship(
        'Group', secondary=tasks_to_groups,
        backref='tasks')
    tracking = db.relationship('TaskTrack', uselist=False, backref='task')


    def __repr__(self):
        return '<Task {}>'.format(self.taskname)

class TaskTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    accepted = db.Column(db.DateTime)
    done = db.Column(db.DateTime)
    approved = db.Column(db.DateTime)

    def __repr__(self):
        return '<Track for task id {}>'.format(self.task_id)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rolename = db.Column(db.String(10), unique=True)
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role {}>'.format(self.rolename)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(20), unique=True)
    description = db.Column(db.String(140))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def add_member(self, username):
        user = User.query.filter_by(username=username).first()
        self.members.append(user)

    def __repr__(self):
        return '<Group {}>'.format(self.groupname)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    balance = db.Column(db.Integer)

    def __repr__(self):
        return '<Account balance {}>'.format(self.balance)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))