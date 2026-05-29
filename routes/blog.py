"""
routes/blog.py — Blog routes for Khushi Decors.
"""
from flask import Blueprint, render_template, request, abort
from extensions import db_sql
from models import BlogPost

bp = Blueprint("blog", __name__, url_prefix="/blog")


@bp.route("")
def blog_list():
    page = request.args.get("page", 1, type=int)
    per_page = 9
    try:
        pagination = BlogPost.query.filter_by(published=1).order_by(BlogPost.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        posts = pagination.items
        total = pagination.total
    except Exception:
        posts, total = [], 0
    return render_template("blog_list.html", posts=posts, page=page, total=total, per_page=per_page)


@bp.route("/<slug>")
def blog_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, published=1).first()
    if not post:
        abort(404)
    return render_template("blog_detail.html", post=post)
