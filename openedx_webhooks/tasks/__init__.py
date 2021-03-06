import sys
import logging
from celery.utils.log import get_task_logger
from flask import Blueprint, jsonify
from openedx_webhooks import celery
from openedx_webhooks.oauth import github_bp, jira_bp

# set up logging
logger = get_task_logger(__name__)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s [%(name)s]')
stderr_handler.setFormatter(formatter)
logger.addHandler(stderr_handler)


# create a Flask blueprint for getting task status info
tasks = Blueprint('tasks', __name__)

@tasks.route('/status/<task_id>')
def status(task_id):
    result = celery.AsyncResult(task_id)
    return jsonify({
        "status": result.state,
        "info": result.info,
    })

@tasks.route('/status/group:<group_id>')
def group_status(group_id):
    # NOTE: This will only work if the GroupResult
    # has previously called .save() on itself
    group_result = celery.GroupResult.restore(group_id)
    completed_task_ids = []
    failed_task_ids = []
    pending_task_ids = []
    for result in group_result.results:
        if result.successful():
            completed_task_ids.append(result.id)
        elif result.failed():
            failed_task_ids.append(result.id)
        else:
            pending_task_ids.append(result.id)
    return jsonify({
        "task_count": len(group_result.results),
        "completed_task_count": len(completed_task_ids),
        "completed_task_ids": completed_task_ids,
        "failed_task_count": len(failed_task_ids),
        "failed_task_info": failed_task_ids,
        "pending_task_count": len(pending_task_ids),
        "pending_task_info": pending_task_ids,
    })


# Working in a Celery task means we can't take advantage of Flask-Dance's
# session proxies, so we'll explicitly define the sessions here.
github_session = github_bp.session
jira_session = jira_bp.session
