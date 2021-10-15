from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres@localhost:5432/todoapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Defining the Todo item model 

class Todo(db.Model): 
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)

    def __repr__(self): 
        return f'<Todo {self.id} {self.description}>'


# Defining the List item model

class TodoList(db.Model): 
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    todos = db.relationship('Todo',backref='list',lazy=True)

# Create a todo item route handler
@app.route('/todos/create', methods=['POST'])
def create_todo():
    body = {}
    error = False
    try: 
        description = request.get_json()['description']
        list_id = request.get_json()['list_id']
        new_task = Todo(description=description, list_id=list_id)
        db.session.add(new_task)
        db.session.commit()
        body['description'] = new_task.description
        body['list_id'] = new_task.list_id
    except: 
        db.session.rollback()
        error = True
        print(sys.exc_info())

    finally: 
        db.session.close()
    
    if error: 
        abort(400)
    
    if not error: 
        return jsonify(body)

# Create lists

@app.route('/lists/create', methods=['POST'])
def create_list():
    body = {}
    error = False
    try: 
        name = request.get_json()['name']
        new_list = TodoList(name=name)
        db.session.add(new_list)
        db.session.commit()
        body['name'] = new_list.name
    except: 
        db.session.rollback()
        error = True
        print(sys.exc_info())

    finally: 
        db.session.close()
    
    if error: 
        abort(400)
    
    if not error: 
        return jsonify(body)


# todo checkbox route handler

@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed(todo_id):
    try: 
        completed = request.get_json()['completed']
        todo_item = Todo.query.get(todo_id)
        todo_item.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('index'))

# list checkbox route handler

@app.route('/lists/<list_id>/set-completed', methods=['POST'])
def list_completed(list_id):
    error = False
    try: 
        completed = request.get_json()['completed']
        list_item = TodoList.query.get(list_id)
        list_item.completed = completed
        for todo in list_item.todos: 
            todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
        error=True
    finally:
        db.session.close()

    if error:
        abort(500)
    else: 
        return redirect(url_for('get_list_todos', list_id=list_id))


# Delete button route handler
@app.route('/todos/<todo_id>/delete', methods=['DELETE'])
def delete_item(todo_id): 
    try: 
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except: 
        print('error!!!!')
        db.session.rollback()
    finally: 
        db.session.close()

    return jsonify({'success':True})

# Delete list route handler
@app.route('/lists/<list_id>/delete', methods=['DELETE'])
def delete_list(list_id):
    try: 
        list = TodoList.query.get(list_id)
        for todo in list.todos:
            db.session.delete(todo)
        db.session.delete(list)
        db.session.commit()
    except: 
        print('error!!!!')
        db.session.rollback()
    finally: 
        db.session.close()

    return jsonify({'success':True})

# Homepage route handler

@app.route('/lists/<list_id>')
def get_list_todos(list_id): 
    return render_template('index.html', 
    todos=Todo.query.filter_by(list_id=list_id).order_by('id').all(),
    lists=TodoList.query.order_by('id').all(),
    active_list = TodoList.query.get(list_id)
    )

@app.route('/')
def index(): 
    return redirect(url_for('get_list_todos', list_id=1))