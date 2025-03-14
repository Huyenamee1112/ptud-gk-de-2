from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Task
from app.forms import TaskForm
from datetime import datetime

bp = Blueprint('main', __name__)

def get_overdue_tasks():
    """Get overdue tasks for the current user"""
    now = datetime.utcnow()
    return Task.query.filter(
        Task.user_id == current_user.id,
        Task.status != 'completed',
        Task.due_date < now
    ).all()

@bp.context_processor
def inject_overdue_tasks():
    """Inject overdue tasks count into all templates"""
    if current_user.is_authenticated:
        overdue_tasks = get_overdue_tasks()
        return {'overdue_tasks_count': len(overdue_tasks)}
    return {'overdue_tasks_count': 0}

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc()).all()
    overdue_tasks = get_overdue_tasks()
    return render_template('index.html', title='Home', tasks=tasks, overdue_tasks=overdue_tasks)

@bp.route('/task/new', methods=['GET', 'POST'])
@login_required
def new_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            user_id=current_user.id,
            due_date=form.due_date.data
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully!')
        return redirect(url_for('main.index'))
    return render_template('task/new.html', title='New Task', form=form)

@bp.route('/task/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('You cannot edit this task.')
        return redirect(url_for('main.index'))
        
    form = TaskForm()
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.status = form.status.data
        task.due_date = form.due_date.data
        if task.status == 'completed' and not task.finished:
            task.finished = datetime.utcnow()
        elif task.status != 'completed':
            task.finished = None
        db.session.commit()
        flash('Task updated successfully!')
        return redirect(url_for('main.index'))
        
    elif request.method == 'GET':
        form.title.data = task.title
        form.description.data = task.description
        form.status.data = task.status
        form.due_date.data = task.due_date
        
    return render_template('task/edit.html', title='Edit Task', form=form)

@bp.route('/task/<int:id>/delete')
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('You cannot delete this task.')
        return redirect(url_for('main.index'))
        
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!')
    return redirect(url_for('main.index')) 